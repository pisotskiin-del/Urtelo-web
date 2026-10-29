"""Переход на новый месяц (форма nov_mes старой программы).

Порядок тот же, что в кнопке «ДА» формы:
1. Архив месяца: состояние potreb, danrasch, polez_otpusk, polez_tarif (файлы
   Po/Da/Ot/ta в Arhiv) — здесь одна запись MesArhiv. Туда же кладутся gvs_kot и
   abot, чтобы последний переход можно было отменить.
2. baza_buh: таблица abot для 1С — абоненты с начислением больше нуля.
3. Запись в журнале arhiv (дата, месяц, год закрытого месяца).
4. Следующий месяц во всех городах danrasch.
5. По каждому абоненту: с начала финансового года (с января) и с начала
   отопительного сезона (с октября) накапливается nac_vsego, пересчитывается
   остаток лимита; начисления и дни обнуляются, показания prev = new.
6. Нагрузка котельных gvs_kot.nagr_kot обнуляется.
Предоплата не используется (решение 28.10.2026), её ветка в baza_buh пропущена.
"""

import datetime
from dataclasses import dataclass
from pathlib import Path
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from catalogs.models import Abot, Arhiv, Danrasch, GvsKot, PolezOtpusk, PolezTarif, Potreb, Tarif

from .models import MesArhiv

MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август",
          "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

# Обнуляются после закрытия месяца (REPLACE … WITH 0 ALL).
ZERO = ["nach_otsub", "nach_otopl", "nacs_priso", "nach_gvs", "nac_vsego", "nach_otnag", "nach_otpr", "poter_gvs",
        "nac_pogaz", "poter_pr", "poter_nag", "gkl_perer", "predopl", "dn_pereras", "tkf_perer",
        "dngvs", "dnotop", "poterschob", "poternagob"]
# Все поля potreb, которые меняет переход (их же возвращает отмена).
CHANGED = ZERO + ["nach_finan", "nach_otopi", "ost_limit", "vd_limit", "pok_old"]

# Выгрузка в 1С по категории потребителя: (код услуги, код услуги 1, № тарифа, название
# категории). Исходник baza_buh.prg на диске старше программы (urteplo.exe 2026 г.),
# поэтому коды сняты с последних 3000 записей dbf\abot.dbf, которые программа писала сама.
USLUGA = {
    1: (4, 4, 1, "Хозрасчет"),
    2: (8, 5, 2, "Местный бюджет"),
    3: (8, 6, 2, "Республиканский бюджет"),
    4: (10, 10, 3, "Население бюджет"),
    5: (5, 9, 3, "Население хозрасчет"),
    6: (5, 8, 3, "Население Абонентское"),
    7: (33, 14, 10, "Организация СКиОД"),
}
KODABON_BASE = 200000  # KODABON = 200000 + код абонента (cod_ac)


def next_month(mes, god):
    return (1, god + 1) if mes >= 12 else (mes + 1, god)


def _q(model, name, value):
    places = model._meta.get_field(name).decimal_places
    return Decimal(value).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def current():
    """Текущий расчетный месяц: (месяц, год) по первому городу danrasch."""
    d = Danrasch.objects.order_by("cod_gorod").first()
    return (d.nom_mes, d.god) if d else (None, None)


@dataclass
class Result:
    closed: tuple
    opened: tuple
    potreb: int
    abot: int
    nac_vsego: Decimal


def _rows(model):
    return list(model.objects.order_by("pk").values())


@transaction.atomic
def run(user=""):
    mes, god = current()
    if mes is None:
        raise ValueError("Нет данных для расчета (danrasch пуст)")
    potrebs = list(Potreb.objects.order_by("pk"))
    total = sum((p.nac_vsego or 0 for p in potrebs), Decimal(0))

    # 1. Архив.
    arh = MesArhiv(nom_mes=mes, god=god, user=user, potreb_count=len(potrebs), nac_vsego=total)
    arh.set_tables({
        "potreb": _rows(Potreb), "danrasch": _rows(Danrasch), "polez_otpusk": _rows(PolezOtpusk),
        "polez_tarif": _rows(PolezTarif), "gvs_kot": [{"pk": k.pk, "nagr_kot": k.nagr_kot} for k in GvsKot.objects.all()],
        "abot": _rows(Abot),
    })
    arh.save()

    # 2. abot для 1С.
    tarifs = {t.id_tar: t.zn_tar or 0 for t in Tarif.objects.all()}
    cities = {d.cod_gorod: d.name_gorod for d in Danrasch.objects.all()}
    abot = []
    for p in potrebs:
        if not (p.nac_vsego or 0) > 0:
            continue
        usl, usl1, tar, kateg = USLUGA.get(p.id_kategor, (None, None, None, ""))
        acc = p.accept or 0
        abot.append(Abot(
            kod=p.cod_buhg, kodabon=KODABON_BASE + (p.cod_ac or 0), name=p.name_potre, akcept=acc - 1 if acc else 0,
            tarif=tarifs.get(tar, 0), ras_kol=_q(Abot, "ras_kol", p.nac_vsego), koduslug=usl, nameuslug="",
            tarifue=0, city=p.cod_gor_id, ras_chet=p.ras_chet, fisk_cod=p.fisk_cod, perc_peni=p.perc_peni or 0,
            koduslug1=usl1, name_city=cities.get(p.cod_gor_id, ""), name_kateg=kateg,
            n_dog=str(p.nom_dog or "").rjust(10), dat_dog=p.data_dog))
    Abot.objects.all().delete()
    Abot.objects.bulk_create(abot)
    tables = arh.tables()
    tables["abot_1c"] = _rows(Abot)
    arh.set_tables(tables)
    arh.save(update_fields=["data"])

    # 3. Журнал закрытых месяцев.
    Arhiv.objects.create(data_arh=timezone.localdate(), god=god, nom_mes=mes)

    # 4. Новый месяц во всех городах.
    new_mes, new_god = next_month(mes, god)
    Danrasch.objects.update(nom_mes=new_mes, name_mes=MONTHS[new_mes - 1], god=new_god)

    # 5. Накопления, лимит, обнуление.
    for p in potrebs:
        if new_mes == 1:
            p.nach_finan = p.ost_limit = p.vd_limit = 0
        if new_mes == 10:
            p.nach_otopi = 0
        vsego = p.nac_vsego or 0
        p.nach_finan = _q(Potreb, "nach_finan", (p.nach_finan or 0) + vsego)
        p.nach_otopi = _q(Potreb, "nach_otopi", (p.nach_otopi or 0) + vsego)
        p.ost_limit = _q(Potreb, "ost_limit", p.vd_limit - p.nach_finan) if (p.vd_limit or 0) > 0 else 0
        for name in ZERO:
            setattr(p, name, 0)
        p.pok_old = p.pok_new
    Potreb.objects.bulk_update(potrebs, CHANGED, batch_size=200)

    # 6. Нагрузка котельных.
    GvsKot.objects.update(nagr_kot=0)
    return Result((mes, god), (new_mes, new_god), len(potrebs), len(abot), total)


def last():
    return MesArhiv.objects.order_by("-pk").first()


@transaction.atomic
def undo():
    """Отменить последний переход: вернуть potreb, danrasch, gvs_kot и abot как
    было до него. Возвращает отменённый архив."""
    arh = last()
    if arh is None:
        raise ValueError("Нет закрытых месяцев")
    t = arh.tables()
    pk = Potreb._meta.pk.attname
    old = {row[pk]: row for row in t["potreb"]}
    potrebs = list(Potreb.objects.filter(pk__in=old))
    for p in potrebs:
        for name in CHANGED:
            setattr(p, name, Potreb._meta.get_field(name).to_python(old[p.pk][name]))
    Potreb.objects.bulk_update(potrebs, CHANGED, batch_size=200)
    for row in t["danrasch"]:
        Danrasch.objects.filter(pk=row[Danrasch._meta.pk.attname]).update(
            nom_mes=row["nom_mes"], name_mes=row["name_mes"], god=row["god"])
    for row in t["gvs_kot"]:
        GvsKot.objects.filter(pk=row["pk"]).update(nagr_kot=GvsKot._meta.get_field("nagr_kot").to_python(row["nagr_kot"]))
    Abot.objects.all().delete()
    Abot.objects.bulk_create([Abot(**{k: v for k, v in r.items() if k != Abot._meta.pk.attname}) for r in t["abot"]])
    Arhiv.objects.filter(nom_mes=arh.nom_mes, god=arh.god).order_by("-pk").first().delete()
    arh.delete()
    return arh


def abot_filename(mes, god):
    """Имя файла как в старой программе: Abot<ГГ><ММ>.dbf за закрытый месяц."""
    return f"Abot{god % 100:02d}{mes:02d}.dbf"


def abot_rows(arh):
    """Строки выгрузки в 1С закрытого месяца (из архива) с именами полей DBF."""
    return [{k.upper(): v for k, v in row.items()} for row in arh.tables().get("abot_1c", [])]


def write_abot(arh, target):
    """Записать файл выгрузки в 1С: target — путь или открытый файл."""
    from .dbf_out import ABOT_FIELDS, write
    rows = abot_rows(arh)
    for row in rows:
        if isinstance(row.get("DAT_DOG"), str):
            row["DAT_DOG"] = datetime.date.fromisoformat(row["DAT_DOG"])
    write(target, ABOT_FIELDS, rows)
    return len(rows)


def export_1c(arh):
    """Положить файл в папку для 1С, если она задана (TEPLO_1C_DIR, в старой
    программе \\SERVER-B\Abon_teplo1C). Возвращает путь или None."""
    from django.conf import settings
    folder = getattr(settings, "TEPLO_1C_DIR", "")
    if not folder:
        return None
    path = Path(folder) / abot_filename(arh.nom_mes, arh.god)
    write_abot(arh, path)
    return path
