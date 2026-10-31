"""Расчет начислений (кнопка «Расчет» формы karta старой программы).

Перенесён по шагам, в том же порядке и с теми же условиями, что в старой
программе: расчёт идёт по всем абонентам всех городов в порядке записей
таблицы potreb. Каждое записанное значение округляется до знаков поля, как
при REPLACE в DBF, и следующие шаги читают уже округлённое значение.

Как в программе 2026 года (urteplo.exe): рассчитываются только абоненты с
заключённым договором (SET FILTER TO d_stat=60), остальные записи расчёт не
трогает и не видит; ГВС по прибору считается по показаниям счетчика ГВС;
к оплате прибавляются тепловые потери ГВС.

Отличия от старой программы:
- договоры со статусом «Возобновлен» (62) тоже рассчитываются (в старой
  программе фильтр пропускал их, а это заключённый договор);
- предоплатой не пользуются (28.10.2026), поэтому ветки «Выставить
  предоплату» и «Удалить предоплату» не перенесены: в старой форме эти
  флажки всегда недоступны. pr_tiprasch старая программа всегда ставит 2."""

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from catalogs.models import Danrasch, Limit, Potreb, SpTeplpoteri

from .layout import RASCHET
from .poteri import SECTIONS, section_loss

ZERO = Decimal(0)
GVS_GKAL = Decimal("0.0533")  # Гкал на единицу показаний счетчика ГВС
POSLE = ["posle_prib", "posle_pri1", "posle_pri2", "posle_pri3", "posle_pri4"]
PRIS_NAG = [f"pris_nag{i}" for i in range(1, 9)]


def n(value):
    """Пустое числовое поле DBF читается как 0."""
    return ZERO if value is None else Decimal(value)


def round2(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Table:
    """Записи одной модели и запись значений с округлением до знаков поля."""

    def __init__(self, model):
        self.places = {f.attname: f.decimal_places for f in model._meta.concrete_fields
                       if f.get_internal_type() == "DecimalField"}
        self.changed = set()

    def put(self, rec, name, value):
        places = self.places.get(name)
        if places is not None:
            value = Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        setattr(rec, name, value)
        self.changed.add(name)


@dataclass
class Result:
    potreb: int = 0
    created_poteri: list = field(default_factory=list)   # л/№, для которых создана запись потерь
    zero_division: list = field(default_factory=list)    # (л/№, что считалось)
    limits: list = field(default_factory=list)          # записи таблицы limit
    cities: list = field(default_factory=list)          # итоги по городам
    otkluchen: list = field(default_factory=list)       # л/№, которые не рассчитывались (договор не заключён)


def _div(a, b, result, rec, what):
    if b == 0:
        if a != 0:
            result.zero_division.append((rec.potreb_id, what))
        return ZERO
    return a / b


@transaction.atomic
def run():
    """Рассчитать всех абонентов и записать результат в базу."""
    recs = list(Potreb.objects.order_by("pk"))
    cities = {d.cod_gorod: d for d in Danrasch.objects.exclude(cod_gorod=None)}
    sp_by_ln = {}
    for sp in SpTeplpoteri.objects.order_by("pk"):
        sp_by_ln.setdefault(sp.ln, sp)
    old_sp = list(sp_by_ln.values())

    result, pt, st = compute(recs, cities, sp_by_ln)

    new_sp = [sp_by_ln[ln] for ln in result.created_poteri]
    SpTeplpoteri.objects.bulk_create(new_sp)
    if st.changed and old_sp:
        SpTeplpoteri.objects.bulk_update(old_sp, sorted(st.changed), batch_size=200)
    if pt.changed:
        Potreb.objects.bulk_update(recs, sorted(pt.changed), batch_size=200)
    Danrasch.objects.bulk_update(list(cities.values()), ["qpras"])
    Limit.objects.all().delete()
    Limit.objects.bulk_create(result.limits)
    return result


def compute(recs, cities, sp_by_ln):
    """Расчет над записями в памяти: recs — абоненты в порядке таблицы,
    cities — danrasch по коду города, sp_by_ln — потери по участкам по л/№
    (недостающие добавляются). Возвращает итоги и какие поля изменены."""
    result = Result()
    result.otkluchen = [p.potreb_id for p in recs if p.d_stat not in RASCHET]
    skipped = [p for p in recs if p.d_stat not in RASCHET]
    recs = [p for p in recs if p.d_stat in RASCHET]
    result.potreb = len(recs)
    pt = Table(Potreb)
    st = Table(SpTeplpoteri)
    put = pt.put
    # У счета без договора не должно оставаться «Предъявлено к оплате»: туда
    # мог попасть итог договора от прежнего расчета (шаг 9 собирает его на
    # последнем абоненте договора), а сам счет больше не рассчитывается.
    for p in skipped:
        if n(p.nac_vsego) != 0:
            put(p, "nac_vsego", 0)

    by_id = {}
    for r in recs:
        by_id.setdefault(r.potreb_id, r)

    def locate(potreb_id):
        # LOCATE FOR potreb_id=...; не найдено — указатель в конце таблицы,
        # поля читаются пустыми.
        return by_id.get(potreb_id)

    def val(rec, name):
        return n(getattr(rec, name)) if rec is not None else ZERO

    # 1. Потери по участкам, обнуление итогов, начисление по прибору и по нагрузке.
    for p in recs:
        sp = sp_by_ln.get(p.potreb_id)
        if sp is None:
            sp = SpTeplpoteri(ln=p.potreb_id)
            sp_by_ln[p.potreb_id] = sp
            result.created_poteri.append(p.potreb_id)
        pr_pot = ZERO
        for i in SECTIONS:
            loss = section_loss(getattr(sp, f"diametr{i}"), n(getattr(sp, f"dlina{i}")), n(p.dnotop))
            st.put(sp, f"poteri_pr{i}", loss)
            pr_pot += loss
        st.put(sp, "vs_poteri", pr_pot)

        tip, nalich = p.tip_rasot, p.nalich_pot
        delta = n(p.pok_new) - n(p.pok_old)
        if tip == 1:
            if nalich == 3:
                put(p, "poter_pr", 0)
            elif nalich == 1:
                put(p, "poter_pr", pr_pot if delta > 0 else 0)
            elif nalich == 2:
                put(p, "poter_pr", pr_pot if delta > 0 or n(p.nom_pribor) > 0 else 0)
        put(p, "poter_nag", pr_pot if n(p.q_otoppr) > 0 and tip in (2, 3) else 0)
        for name in ("nach_otpr", "nacs_priso", "nach_otsub", "nach_otnag", "nac_pogaz", "nach_otopl",
                     "nac_vsego", "poterschob", "poternagob"):
            put(p, name, 0)
        if n(p.dn_pereras) != 0:
            put(p, "gkl_perer", n(p.q_otoppr) * 24 * n(p.dn_pereras) * n(p.tkf_perer))
        city = cities.get(p.cod_gor_id)
        tkoef = n(city.tkoef) if city else ZERO
        po_nagruzke = n(p.q_otoppr) * 24 * n(p.dnotop) * tkoef
        if tip == 1:
            put(p, "nach_otpr", delta * n(p.koef_pok))
            put(p, "nach_otnag", 0)
        elif tip == 2:
            put(p, "nach_otpr", delta * n(p.koef_pok))
            put(p, "nach_otnag", po_nagruzke)
        elif tip == 3:
            put(p, "nach_otnag", po_nagruzke)
            put(p, "nach_otpr", 0)
        put(p, "s_obshaya", 0)
        put(p, "q_otopobsh", 0)
        if p.tip_rasgvs == 1:
            put(p, "nach_gvs", (n(p.pok_newg) - n(p.pok_oldg)) * GVS_GKAL)

    # 2. Абоненты (не главные по договору), у которых потери начисляются.
    for p in recs:
        if n(p.nom_dog) > 0 and n(p.nom_dog) != n(p.nom_dogab) and p.nalich_pot in (1, 2):
            put(p, "s_obshaya", n(p.s_potreb))
            put(p, "q_otopobsh", n(p.q_otop))
            if p.nalich_pot == 1 and n(p.q_otopobsh) > 0:
                put(p, "poterschob", round2(n(p.q_otop) / n(p.q_otopobsh) * n(p.poter_pr)))
                put(p, "poternagob", round2(n(p.q_otop) / n(p.q_otopobsh) * n(p.poter_nag)))
            elif p.nalich_pot == 2:
                put(p, "poterschob", n(p.poter_pr))
                put(p, "poternagob", n(p.poter_nag))

    # 3. Общая площадь здания у главного по договору.
    for p in recs:
        if n(p.nom_dog) > 0 and n(p.nom_dog) == n(p.nom_dogab):
            put(p, "s_obshaya", sum((n(r.s_potreb) for r in recs
                                     if n(r.nom_dogab) == n(p.nom_dog) and r.cod_gor_id == p.cod_gor_id
                                     and r.nalich_pot == 1), ZERO))

    # 4. Начислено с присоединённых приборов.
    for p in recs:
        nums = [n(getattr(p, name)) for name in POSLE]
        if sum(nums) > 0:
            put(p, "nacs_priso", sum((val(locate(nom), "nach_otpr") for nom in nums if nom > 0), ZERO))

    # 5. Распределение по присоединённой нагрузке.
    for p in recs:
        nums = [n(getattr(p, name)) for name in PRIS_NAG]
        if sum(nums) <= 0:
            continue
        nom0 = sum((val(locate(nom), "q_otop") for nom in nums if nom > 0), ZERO)
        proc_nach = _div(n(p.nach_otpr) - n(p.nacs_priso), n(p.q_otop) + nom0, result, p,
                         "присоединённая нагрузка")
        poslpr = ZERO
        for nom in nums:
            r = locate(nom) if nom > 0 else None
            if r is not None:
                put(r, "nach_otnag", proc_nach * n(r.q_otoppr))
                poslpr += n(r.nach_otnag)
        put(p, "nacs_priso", n(p.nacs_priso) + poslpr)

    # 6. Начисления субабонентам договора по общему прибору.
    for p in recs:
        if not (n(p.nom_dog) > 0 and n(p.nom_dog) == n(p.nom_dogab)):
            continue
        group = [r for r in recs if n(r.nom_dogab) == n(p.nom_dog) and n(r.nom_pribor) == n(p.nom_pribor)
                 and r.cod_gor_id == p.cod_gor_id]
        qobsh = sum((n(r.q_otop) for r in group), ZERO)
        qobsh1 = sum((n(r.q_otop) for r in group if r.nalich_pot == 1), ZERO)
        nach_otop = n(p.nach_otpr) - n(p.nacs_priso)
        pr_poter, pr_potern = n(p.poter_pr), n(p.poter_nag)
        for r in group:
            put(r, "nach_otsub", _div(nach_otop, qobsh, result, p, "нагрузка субабонентов договора") * n(r.q_otop))
            if r.nalich_pot == 3:
                put(r, "poterschob", 0)
                put(r, "poternagob", 0)
            elif r.nalich_pot == 1 and qobsh1 > 0:
                put(r, "poterschob", round2(n(r.q_otop) / qobsh1 * pr_poter))
                put(r, "poternagob", round2(n(r.q_otop) / qobsh1 * pr_potern))
            elif r.nalich_pot == 2:
                put(r, "poterschob", n(r.poter_pr))
                put(r, "poternagob", n(r.poter_nag))
        put(p, "q_otopobsh", qobsh)

    # 7. Начислено по факту: фактический отпуск города сверх приборов и ГВС
    # делится пропорционально начисленному по нагрузке.
    totals = {}
    for code, city in sorted(cities.items()):
        in_city = [r for r in recs if r.cod_gor_id == code]
        otpr = sum((n(r.nach_otpr) for r in in_city), ZERO)
        gvs = sum((n(r.nach_gvs) for r in in_city), ZERO)
        nacotnag = sum((n(r.nach_otnag) for r in in_city), ZERO)
        ostatok = n(city.qpfakt) - otpr - gvs
        for r in in_city:
            if n(r.dnotop) > 0 and ostatok > 0:
                if nacotnag == 0:
                    put(r, "nac_pogaz", ostatok * n(r.nach_otnag))
                else:
                    put(r, "nac_pogaz", ostatok / nacotnag * n(r.nach_otnag))
        city.qpras = nacotnag
        totals[code] = {"otpr": otpr, "gvs": gvs, "nacotnag": nacotnag}

    # 8. Фактическое потребление и предъявлено к оплате.
    for p in recs:
        if n(p.nac_pogaz) > n(p.nach_otnag) or n(p.nac_pogaz) == 0:
            otopnag = n(p.nach_otnag)
        else:
            otopnag = n(p.nac_pogaz)
        poteri_ob = n(p.poternagob) if otopnag > 0 else n(p.poterschob)
        if n(p.nom_dog) > 0 and n(p.nom_dog) != n(p.nom_dogab):
            put(p, "nach_otopl", round2(n(p.nach_otpr) + n(p.nach_otsub) + otopnag + n(p.gkl_perer)
                                        + poteri_ob - n(p.nacs_priso)))
        else:
            put(p, "nach_otopl", round2(n(p.nach_otsub) + otopnag + n(p.gkl_perer) + poteri_ob))
        put(p, "nac_vsego", n(p.nach_gvs) + n(p.nach_otopl) + n(p.poter_gvs))

    # 9. Объекты одного договора (otnos_dog): к оплате собирается на абоненте.
    for p in recs:
        if not (p.id_katabon == 1 and n(p.otnos_dog) > 0):
            continue
        nom2, gorod = n(p.otnos_dog), p.cod_gor_id
        nac_ob = ZERO
        for r in recs:
            if n(r.otnos_dog) == nom2 and r.id_katabon == 1 and r.cod_gor_id == gorod:
                nac_ob += n(r.nac_vsego)
                put(r, "nac_vsego", 0)
        for r in recs:
            if n(r.otnos_dog) == nom2 and r.id_katabon == 3 and r.cod_gor_id == gorod:
                nac_ob += n(r.nac_vsego)
                put(r, "nac_vsego", 0)
        put(p, "nac_vsego", nac_ob + n(p.nac_vsego))

    # 10. Лимиты.
    limits = []
    for p in recs:
        if n(p.vd_limit) > 0 and n(p.nach_finan) + n(p.nac_vsego) * 2 >= n(p.vd_limit):
            over = n(p.nach_finan) + n(p.nac_vsego) > n(p.vd_limit)
            limits.append(Limit(
                koment="Превышение лимита" if over else "Лимит заканчивается",
                nach_finan=n(p.nach_finan), nac_vsego=n(p.nac_vsego), name_dog=(p.name_potre or "")[:150],
                potreb_id=p.potreb_id, vd_limit=n(p.vd_limit),
            ))

    result.limits = limits
    for code, city in sorted(cities.items()):
        in_city = [r for r in recs if r.cod_gor_id == code]
        row = {"city": city, "count": len(in_city), **totals[code]}
        for name in ("nac_pogaz", "nach_otopl", "nac_vsego", "poter_pr", "poter_nag"):
            row[name] = sum((n(getattr(r, name)) for r in in_city), ZERO)
        result.cities.append(row)
    return result, pt, st
