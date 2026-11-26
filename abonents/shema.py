"""Блок-схема расчета (кнопка «Блок-схема расчета» на экране «Исходные данные
для расчета» и в карточке абонента).

Четыре схемы: начисление отопления, начисление ГВС, перерасчет отопления и
перерасчет ГВС. Шаги и условия те же, что в abonents/raschet.py. Схема
динамическая: расчет выполняется в памяти по текущим данным базы (как кнопка
«Расчет», но без записи), и на каждом шаге показано значение и какая ветка
сработала. Для одного абонента — его числа; для города — сколько абонентов
прошло по каждой ветке и сумма по ним."""

import copy
from decimal import Decimal

from catalogs.models import Danrasch, Potreb, SpTeplpoteri

from . import layout
from .raschet import GVS_GKAL, POSLE, PRIS_NAG, ZERO, compute, n

VIDY = [
    ("otop", "Начисление отопления", "flame"),
    ("gvs", "Начисление ГВС", "drop"),
    ("perer_otop", "Перерасчет отопления", "thermo"),
    ("perer_gvs", "Перерасчет ГВС", "gauge"),
]

# Поля, значения которых расчет перезаписывает: показываем и «в базе».
RESULT_FIELDS = ["poter_pr", "poter_nag", "nach_otpr", "nach_otnag", "nacs_priso", "nach_otsub", "poterschob",
                 "poternagob", "nac_pogaz", "nach_otopl", "nac_vsego", "nach_gvs", "gkl_perer"]


def fmt(value):
    """Число по-русски: пробел между тысячами, запятая, без лишних нулей."""
    if value is None:
        return ""
    value = Decimal(value)
    if value == value.to_integral_value():
        value = value.quantize(Decimal(1))
    else:
        if value.as_tuple().exponent < -4:
            value = value.quantize(Decimal("0.0001"))
        value = value.normalize()
    text = format(value, "f")
    sign = "−" if text.startswith("-") else ""
    text = text.lstrip("-")
    whole, _, frac = text.partition(".")
    groups = []
    while len(whole) > 3:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    groups.insert(0, whole)
    return sign + " ".join(groups) + ("," + frac if frac else "")


# --- узлы схемы ---------------------------------------------------------------

def step(title, formula="", value=None, unit="Гкал", active=True, subst="", note="", field=None, city=False):
    return {"kind": "step", "title": title, "formula": formula, "value": value, "unit": unit, "active": active,
            "subst": subst, "note": note, "field": field, "stored": None, "city": city}


def info(title, note=""):
    return {"kind": "info", "title": title, "note": note, "active": True}


def end(title, value=None, unit="Гкал", active=True, field=None):
    return {"kind": "end", "title": title, "value": value, "unit": unit, "active": active, "field": field,
            "stored": None, "formula": "", "subst": "", "note": "", "city": False}


def decision(title, question, branches, active=True):
    return {"kind": "decision", "title": title, "question": question, "branches": branches, "active": active}


def branch(label, active, nodes=()):
    return {"label": label, "active": active, "nodes": list(nodes)}


# --- данные для схемы ---------------------------------------------------------

class Data:
    """Расчет в памяти по текущим данным и то, что нужно схеме сверх него."""

    def __init__(self):
        recs = list(Potreb.objects.select_related("cod_gor").order_by("pk"))
        self.stored = {p.pk: {name: getattr(p, name) for name in RESULT_FIELDS} for p in recs}
        cities = {d.cod_gorod: d for d in Danrasch.objects.exclude(cod_gorod=None)}
        sp_by_ln = {}
        for sp in SpTeplpoteri.objects.order_by("pk"):
            sp_by_ln.setdefault(sp.ln, sp)
        self.qpras_stored = {code: d.qpras for code, d in cities.items()}
        result, _, _ = compute(recs, cities, sp_by_ln)
        self.recs = recs
        self.cities = cities
        self.sp_by_ln = sp_by_ln
        self.totals = {row["city"].cod_gorod: row for row in result.cities}
        self.calc = [p for p in recs if p.d_stat in layout.RASCHET]
        self.by_id = {}
        for r in self.calc:
            self.by_id.setdefault(r.potreb_id, r)
        # Чей прибор раздается абоненту по присоединённой нагрузке (шаг 5).
        self.owner = {}
        for r in self.calc:
            for name in PRIS_NAG:
                nom = n(getattr(r, name))
                if nom > 0 and nom in self.by_id:
                    self.owner[nom] = r
        # Головной договора, по общему прибору которого считается абонент (шаг 6).
        self.head = {}
        for h in self.calc:
            if n(h.nom_dog) > 0 and n(h.nom_dog) == n(h.nom_dogab):
                for r in self.calc:
                    if (n(r.nom_dogab) == n(h.nom_dog) and n(r.nom_pribor) == n(h.nom_pribor)
                            and r.cod_gor_id == h.cod_gor_id):
                        self.head[r.pk] = h
        # Сумма к оплате до сведения объектов одного договора (шаг 9).
        self.vsego8 = {p.pk: n(p.nach_gvs) + n(p.nach_otopl) + n(p.poter_gvs) for p in self.calc}

    def city_recs(self, code):
        return [p for p in self.recs if p.cod_gor_id == code]


class Ctx:
    """Абонент для построения схемы."""

    def __init__(self, data, p):
        self.data, self.p = data, p
        self.on = p.d_stat in layout.RASCHET
        self.city = data.cities.get(p.cod_gor_id)
        self.tot = data.totals.get(p.cod_gor_id, {"otpr": ZERO, "gvs": ZERO, "nacotnag": ZERO})
        sp = data.sp_by_ln.get(p.potreb_id)
        self.pr_pot = n(sp.vs_poteri) if sp is not None and self.on else ZERO
        self.tkoef = n(self.city.tkoef) if self.city else ZERO
        self.qpfakt = n(self.city.qpfakt) if self.city else ZERO
        self.ostatok = self.qpfakt - self.tot["otpr"] - self.tot["gvs"]

    def v(self, name):
        return n(getattr(self.p, name))


def _fill(nodes, ctx, active=True):
    """Подставить значения полей, «в базе» и выключить шаги, если расчет не
    идет (договор не заключён) или ветка не сработала."""
    for node in nodes:
        node["active"] = node["active"] and (active or node.get("always", False))
        if node.get("field"):
            if node["value"] is None:
                node["value"] = ctx.v(node["field"])
            stored = ctx.data.stored.get(ctx.p.pk, {}).get(node["field"])
            if ctx.on and node["field"] in RESULT_FIELDS and n(stored) != n(node["value"]):
                node["stored"] = n(stored)
        if node["kind"] == "decision":
            for b in node["branches"]:
                b["active"] = b["active"] and node["active"]
                _fill(b["nodes"], ctx, b["active"])
    return nodes


def _status(ctx):
    p = ctx.p
    stat = dict(layout.D_STAT).get(p.d_stat, "не указан")
    node = decision("Статус договора", "Договор «Заключен» или «Возобновлен»?", [
        branch("да — рассчитывается", ctx.on, [info("Расчет выполняется")]),
        branch("нет — не рассчитывается", not ctx.on,
               [end("Расчет абонента не трогает; «Предъявлено к оплате» обнуляется", ZERO)]),
    ])
    node["always"] = True
    node["subst"] = f"Сейчас: {stat}"
    return node


def _itog(ctx):
    p = ctx.p
    grp = p.id_katabon == 1 and n(p.otnos_dog) > 0
    member = not grp and p.id_katabon in (1, 3) and n(p.otnos_dog) > 0
    return [
        step("Предъявлено к оплате (отопление + ГВС)", "ГВС + фактическое потребление отопления + тепловые потери ГВС",
             ctx.data.vsego8.get(p.pk, ZERO),
             subst=f"{fmt(ctx.v('nach_gvs'))} + {fmt(ctx.v('nach_otopl'))} + {fmt(ctx.v('poter_gvs'))}"),
        decision("Объекты одного договора", "Есть «договора №» (otnos_dog) у абонента или объекта?", [
            branch("абонент группы", grp, [step(
                "К оплате собирается на абоненте", "Σ к оплате абонентов и объектов с тем же «договора №» в городе; "
                "у остальных 0", field="nac_vsego", subst=f"договора № {fmt(p.otnos_dog)}" if grp else "")]),
            branch("объект группы", member, [step("К оплате переносится на абонента группы", "", field="nac_vsego")]),
            branch("нет", not grp and not member, [info("Без изменений")]),
        ]),
        end("Предъявлено к оплате", field="nac_vsego"),
    ]


def tree_otop(ctx):
    p, v = ctx.p, ctx.v
    tip, nalich = p.tip_rasot, p.nalich_pot
    delta = v("pok_new") - v("pok_old")
    po_prib = f"({fmt(v('pok_new'))} − {fmt(v('pok_old'))}) × {fmt(v('koef_pok'))}"
    po_nag = f"{fmt(v('q_otoppr'))} × 24 × {fmt(v('dnotop'))} × {fmt(ctx.tkoef)}"
    nachotpr = lambda: step("Начислено по прибору", "(Показания настоящие − предыдущие) × переводной коэффициент",
                            field="nach_otpr", subst=po_prib)
    nachotnag = lambda: step("Начислено по расчету (по нагрузке)",
                             "Q расчетная, Гкал/ч × 24 × дни отопления × t коэффициент города",
                             field="nach_otnag", subst=po_nag)
    pot_pr = [
        branch("1 — начислять", nalich == 1, [step("Потери по прибору", "= потери сети, если показания выросли; иначе 0",
                                                   field="poter_pr", subst=f"рост показаний {fmt(delta)}")]),
        branch("2 — отдельно", nalich == 2, [step(
            "Потери по прибору", "= потери сети, если показания выросли или указан № сч.; иначе 0", field="poter_pr",
            subst=f"рост показаний {fmt(delta)}, № сч. {fmt(v('nom_pribor'))}")]),
        branch("3 — не начислять", nalich == 3, [step("Потери по прибору", "= 0", field="poter_pr")]),
    ]
    posle = [int(n(getattr(p, name))) for name in POSLE if n(getattr(p, name)) > 0]
    pris = [int(n(getattr(p, name))) for name in PRIS_NAG if n(getattr(p, name)) > 0]
    owner = ctx.data.owner.get(n(p.potreb_id)) if ctx.on else None
    head = ctx.data.head.get(p.pk) if ctx.on else None
    sub = n(p.nom_dog) > 0 and n(p.nom_dog) != n(p.nom_dogab)
    nag_ok = v("dnotop") > 0 and ctx.ostatok > 0
    po_faktu = not (v("nac_pogaz") > v("nach_otnag") or v("nac_pogaz") == 0)
    otopnag = v("nac_pogaz") if po_faktu else v("nach_otnag")
    poteri_ob = v("poternagob") if otopnag > 0 else v("poterschob")
    return [
        _status(ctx),
        step("Тепловые потери в сетях", "Σ по 6 участкам: k(диаметр) × длина × 24 × дни отопления × 0,000001",
             ctx.pr_pot, subst=f"дней отопления {fmt(v('dnotop'))}"),
        decision("Способ расчета отопления", "Как считается потребление?", [
            branch("1 — по прибору", tip == 1, [
                nachotpr(), step("Начислено по расчету", "= 0", field="nach_otnag"),
                decision("Тепловые потери по прибору", "Что выбрано в «Тепловые потери»?", pot_pr)]),
            branch("2 — по прибору и нагрузке", tip == 2, [nachotpr(), nachotnag()]),
            branch("3 — по нагрузке", tip == 3, [step("Начислено по прибору", "= 0", field="nach_otpr"), nachotnag()]),
        ]),
        step("Потери по нагрузке", "= потери сети, если Q расчетная > 0 и способ 2 или 3; иначе 0", field="poter_nag",
             subst=f"Q расчетная {fmt(v('q_otoppr'))}"),
        decision("Присоединённые приборы", "Указаны приборы «после прибора»?", [
            branch("да", bool(posle), [step("Начислено с присоед. приборов",
                                            "Σ «начислено по прибору» присоединённых л/№", field="nacs_priso",
                                            subst=("л/№ " + ", ".join(map(str, posle))) if posle else "")]),
            branch("нет", not posle, [info("Начислено с присоед. приборов = 0")]),
        ]),
        decision("Присоединённая нагрузка", "Делится ли показание прибора по нагрузке?", [
            branch("абонент раздаёт свой прибор", bool(pris), [step(
                "Доля на единицу нагрузки и раздача", "(по прибору − с присоед.) / (Q объекта + Σ Q присоединённых); "
                "присоединённым: доля × их Q расчетная; их сумма прибавляется к «с присоед.»", field="nacs_priso",
                subst=("л/№ " + ", ".join(map(str, pris))) if pris else "")]),
            branch("абонент присоединён к прибору", owner is not None, [step(
                "Начислено по расчету", "доля прибора × Q расчетная", field="nach_otnag",
                subst=f"прибор л/№ {owner.potreb_id}, Q расчетная {fmt(v('q_otoppr'))}" if owner else "")]),
            branch("нет", not pris and owner is None, [info("Без изменений")]),
        ]),
        decision("Общий прибор договора", "Абонент в группе головного договора с тем же № сч.?", [
            branch("да", head is not None, [
                step("Начислено субабоненту", "(по прибору головного − с присоед.) / Σ Q объектов группы × Q объекта",
                     field="nach_otsub",
                     subst=f"головной л/№ {head.potreb_id}, Q объекта {fmt(v('q_otop'))}" if head else ""),
                step("Тепл. потери объекта (по прибору)", "по «Тепловые потери»: 1 — доля по Q, 2 — свои, 3 — 0",
                     field="poterschob"),
                step("Тепл. потери объекта (по нагрузке)", "так же, от потерь по нагрузке", field="poternagob"),
            ]),
            branch("нет", head is None, [info("Начислено субабоненту = 0")]),
        ]),
        step("Остаток фактического отпуска города", "Q факт − Σ по прибору − Σ ГВС по городу", ctx.ostatok,
             subst=f"{fmt(ctx.qpfakt)} − {fmt(ctx.tot['otpr'])} − {fmt(ctx.tot['gvs'])}", city=True),
        decision("Начисление по факту", "Дни отопления > 0 и остаток > 0?", [
            branch("да", nag_ok, [step("Начислено по факту", "остаток / Σ по расчету города × по расчету",
                                       field="nac_pogaz",
                                       subst=f"{fmt(ctx.ostatok)} / {fmt(ctx.tot['nacotnag'])} × {fmt(v('nach_otnag'))}")]),
            branch("нет", not nag_ok, [step("Начислено по факту", "= 0", field="nac_pogaz")]),
        ]),
        decision("Что берётся по нагрузке", "«По факту» = 0 или больше «по расчету»?", [
            branch("да — по расчету", not po_faktu, [step("По нагрузке", "= начислено по расчету",
                                                          otopnag if not po_faktu else None)]),
            branch("нет — по факту (меньшее)", po_faktu, [step("По нагрузке", "= начислено по факту",
                                                               otopnag if po_faktu else None)]),
        ]),
        decision("Потери объекта", "Есть начисление по нагрузке (> 0)?", [
            branch("да", otopnag > 0, [step("Потери", "= тепл. потери объекта по нагрузке",
                                            poteri_ob if otopnag > 0 else None)]),
            branch("нет", otopnag <= 0, [step("Потери", "= тепл. потери объекта по прибору",
                                              poteri_ob if otopnag <= 0 else None)]),
        ]),
        decision("Фактическое потребление", "Субабонент (№ договора ≠ № головного)?", [
            branch("да", sub, [step("Фактическое потребление",
                                    "по прибору + субабоненту + по нагрузке + перерасчет + потери − с присоед.",
                                    field="nach_otopl",
                                    subst=f"{fmt(v('nach_otpr'))} + {fmt(v('nach_otsub'))} + {fmt(otopnag)} + "
                                          f"{fmt(v('gkl_perer'))} + {fmt(poteri_ob)} − {fmt(v('nacs_priso'))}")]),
            branch("нет", not sub, [step("Фактическое потребление", "субабоненту + по нагрузке + перерасчет + потери",
                                         field="nach_otopl",
                                         subst=f"{fmt(v('nach_otsub'))} + {fmt(otopnag)} + {fmt(v('gkl_perer'))} + "
                                               f"{fmt(poteri_ob)}")]),
        ]),
        *_itog(ctx),
    ]


def tree_gvs(ctx):
    p, v = ctx.p, ctx.v
    tip = p.tip_rasgvs
    return [
        _status(ctx),
        decision("Способ расчета ГВС", "Как считается ГВС?", [
            branch("1 — по прибору", tip == 1, [step(
                "ГВС, фактическое потребление", "(Показания настоящие − предыдущие ГВС) × " + fmt(GVS_GKAL),
                field="nach_gvs", subst=f"({fmt(v('pok_newg'))} − {fmt(v('pok_oldg'))}) × {fmt(GVS_GKAL)}")]),
            branch("2 — по нагрузке", tip != 1, [step(
                "ГВС, фактическое потребление", "расчет не меняет: вводится вручную на вкладке «ГВС»",
                field="nach_gvs", note=f"Q ГВС {fmt(v('q_gvs'))} Гкал/мес, дней ГВС {fmt(v('dngvs'))}")]),
        ]),
        step("Тепловые потери ГВС", "вводятся в карте, расчет не меняет", v("poter_gvs")),
        step("ГВС города уменьшает остаток для «по факту»", "Σ ГВС по городу вычитается из Q факт", ctx.tot["gvs"],
             city=True),
        *_itog(ctx),
    ]


def tree_perer_otop(ctx):
    p, v = ctx.p, ctx.v
    est = v("dn_pereras") != 0
    sub = n(p.nom_dog) > 0 and n(p.nom_dog) != n(p.nom_dogab)
    return [
        _status(ctx),
        decision("Перерасчет т/э", "Указаны дни перерасчета (≠ 0)?", [
            branch("да", est, [step("Перерасчет т/э", "Q расчетная × 24 × дни перерасчета × t коэфф. перерасчета",
                                    field="gkl_perer",
                                    subst=f"{fmt(v('q_otoppr'))} × 24 × {fmt(v('dn_pereras'))} × {fmt(v('tkf_perer'))}")]),
            branch("нет", not est, [step("Перерасчет т/э", "расчет не меняет: остаётся то, что введено в карте",
                                         field="gkl_perer")]),
        ]),
        info("Правка дней перерасчета в карте", "Новое число дней обнуляет t коэфф. и Гкал перерасчета, если их не "
                                                "исправили вместе с ним."),
        step("Перерасчет входит в фактическое потребление отопления",
             ("по прибору + субабоненту + по нагрузке + перерасчет + потери − с присоед." if sub else
              "субабоненту + по нагрузке + перерасчет + потери"), field="nach_otopl",
             subst=f"в т. ч. перерасчет {fmt(v('gkl_perer'))}"),
        *_itog(ctx),
        info("Новый месяц", "При переходе на новый месяц дни, коэффициент и Гкал перерасчета обнуляются."),
    ]


def tree_perer_gvs(ctx):
    p, v = ctx.p, ctx.v
    tip = p.tip_rasgvs
    otkl = p.data_otgvs is not None
    period = (f"с {p.data_otgvs:%d.%m.%Y}" if p.data_otgvs else "") + (
        f" по {p.data_pdgvs:%d.%m.%Y}" if p.data_pdgvs else "")
    akt = (f"акт № {p.nom_aktag or '—'}" + (f" от {p.data_aktag:%d.%m.%Y}" if p.data_aktag else "")
           if p.nom_aktag or p.data_aktag else "")
    return [
        info("Отдельной формулы перерасчета ГВС нет", "Ни в старой программе, ни в расчете веб-версии: перерасчет ГВС "
                                                      "делается исправлением исходных данных ниже."),
        _status(ctx),
        decision("Способ расчета ГВС", "Как исправляется ГВС?", [
            branch("1 — по прибору", tip == 1, [
                info("Исправить показания счетчика ГВС", "Расчет заново посчитает потребление по показаниям."),
                step("ГВС, фактическое потребление", "(настоящие − предыдущие) × " + fmt(GVS_GKAL), field="nach_gvs",
                     subst=f"({fmt(v('pok_newg'))} − {fmt(v('pok_oldg'))}) × {fmt(GVS_GKAL)}")]),
            branch("2 — по нагрузке", tip != 1, [
                info("Исправить «Фактическое потребление» на вкладке «ГВС»", "Расчет это значение не меняет."),
                step("ГВС, фактическое потребление", "введено вручную", field="nach_gvs",
                     note=f"Q ГВС {fmt(v('q_gvs'))} Гкал/мес, дней ГВС {fmt(v('dngvs'))}")]),
        ]),
        decision("Отключение ГВС", "Указано «Отключен с»?", [
            branch("да", otkl, [info("Учесть период отключения", " ".join(x for x in (period.strip(), akt) if x))]),
            branch("нет", not otkl, [info("Отключений нет")]),
        ]),
        step("Тепловые потери ГВС", "вводятся в карте", v("poter_gvs")),
        *_itog(ctx),
        info("Новый месяц", "При переходе на новый месяц ГВС и потери ГВС обнуляются."),
    ]


TREES = {"otop": tree_otop, "gvs": tree_gvs, "perer_otop": tree_perer_otop, "perer_gvs": tree_perer_gvs}


def abonent(data, p):
    """Схемы для одного абонента: {вид: узлы}."""
    ctx = Ctx(data, p)
    trees = {}
    for key, build in TREES.items():
        nodes = build(ctx)
        for node in nodes:
            if node["kind"] == "info" and node is nodes[0]:
                node["always"] = True
        trees[key] = _fill(nodes, ctx, ctx.on)
    return trees


def _merge(acc, nodes):
    """Сложить схему абонента в схему города: счетчик сработавших шагов и
    веток, сумма значений по сработавшим шагам."""
    if acc is None:
        acc = copy.deepcopy(nodes)
        for node in _walk(acc):
            node["count"] = 0
            if "value" in node and not node.get("city"):
                node["value"] = ZERO
            node["stored"] = None
            node["subst"] = node.get("subst") and ""
            if node.get("note") and node["kind"] != "info":
                node["note"] = ""
    for a, b in zip(_walk(acc), _walk(nodes)):
        if b["active"]:
            a["count"] += 1
            if "value" in a and not a.get("city") and b.get("value") is not None:
                a["value"] += n(b["value"])
        if a.get("city") and b.get("value") is not None:
            a["value"] = b["value"]
    return acc


def _walk(nodes):
    for node in nodes:
        yield node
        if node["kind"] == "decision":
            for b in node["branches"]:
                yield b
                yield from _walk(b["nodes"])


def gorod(data, code):
    """Схемы по городу: сколько абонентов прошло по каждой ветке и суммы."""
    result = {}
    for p in data.city_recs(code):
        trees = abonent(data, p)
        for key, nodes in trees.items():
            result[key] = _merge(result.get(key), nodes)
    total = len(data.city_recs(code))
    for nodes in result.values():
        for node in _walk(nodes):
            node["active"] = node["count"] > 0
            node["total"] = total
    return result
