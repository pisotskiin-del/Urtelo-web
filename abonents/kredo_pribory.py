"""Передача в АПК «КРЭДО» приборов учёта и последних показаний.

Повторяет кнопки формы rric старой программы:

- «(Отправка) Информация о приборах учета абонентов» (Command35): справочники
  Set_URDeviceList, Set_URDevTypeList, Set_URDevPlaceList и приборы абонентов
  Set_URDevice — таблицы как есть (Справочники → Приборы учёта и др.);
- «(Отправка) информация о последних показаниях приборов учета абонентов»
  (Command31): по каждому прибору Set_URDevice лицевого участка — показание
  из карты (potreb.pok_new), дата — сегодня, tip_pok = 2, единица измерения
  из справочника приборов (нет в справочнике — «-»).

Отличия от старой программы: приборы передаются только лицевых своего участка
(старая программа отправляла всю таблицу с кодом организации текущего города);
показания не передаются по лицевым без показания в карте (раньше уходил 0).
"""

import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from catalogs.models import Potreb, SetUrdevice, SetUrdevicelist, SetUrdevplacelist, SetUrdevtypelist


def _s(v):
    return ("" if v is None else str(v)).strip()


def _lic(p_kod):
    """potreb_id из p_kod прибора: ROUND(VAL(p_kod), 0)."""
    try:
        return int(Decimal(_s(p_kod)).quantize(Decimal(1)))
    except (InvalidOperation, ValueError):
        return None


def pribory_uchastka(cod_gor):
    """Приборы Set_URDevice лицевых участка: [(прибор, лицевой)] и замечания."""
    licevye = {p.potreb_id: p for p in Potreb.objects.filter(cod_gor=cod_gor)}
    vse = {p_id for p_id in Potreb.objects.values_list("potreb_id", flat=True)}
    out, zamech = [], []
    for d in SetUrdevice.objects.order_by("liz", "p_kod", "pk"):
        n = _lic(d.p_kod)
        p = licevye.get(n)
        if p is not None:
            out.append((d, p))
        elif n not in vse:
            zamech.append(f"Прибор № {_s(d.d_num) or '—'} (p_kod {_s(d.p_kod) or 'пусто'}): нет такого лицевого — не передаётся")
    return out, zamech


def _stroka(obj, proc):
    from .kredo_dogovory import POLYA
    imena = {"del": "del_dbf"}
    return {f: getattr(obj, imena.get(f, f), None) for f, _ in POLYA[proc]}


def pakety_priborov(cod_gor):
    """Справочники и приборы участка: ({процедура: [строка]}, [замечание])."""
    pribory, zamech = pribory_uchastka(cod_gor)
    paket = {
        "Set_URDeviceList": [_stroka(x, "Set_URDeviceList") for x in SetUrdevicelist.objects.order_by("kod", "pk")],
        "Set_URDevTypeList": [_stroka(x, "Set_URDevTypeList") for x in SetUrdevtypelist.objects.order_by("kod", "pk")],
        "Set_URDevPlaceList": [_stroka(x, "Set_URDevPlaceList") for x in SetUrdevplacelist.objects.order_by("kod", "pk")],
        "Set_URDevice": [_stroka(d, "Set_URDevice") for d, _ in pribory],
    }
    return paket, zamech


def pakety_pokazanij(cod_gor, data=None):
    """Последние показания приборов участка: ({"Set_URDeviceMeters": [строка]}, [замечание])."""
    data = data or datetime.date.today()
    edn = {_s(x.kod): _s(x.edn) for x in SetUrdevicelist.objects.all()}
    pribory, zamech = pribory_uchastka(cod_gor)
    rows = []
    for d, p in pribory:
        if p.pok_new is None:
            zamech.append(f"Л/с {p.potreb_id}, прибор № {_s(d.d_num) or '—'}: в карте нет показания — не передаётся")
            continue
        rows.append({
            "liz": _s(d.liz), "p_kod": _s(d.p_kod), "d_kod": _s(d.d_kod), "d_tip": d.d_tip, "d_num": _s(d.d_num),
            "tip_pok": 2, "last_pok": Decimal(p.pok_new).quantize(Decimal("0.01"), ROUND_HALF_UP), "pok_date": data,
            "rric_acn": _s(p.rric_acn), "edn": edn.get(_s(d.d_kod)) or "-",
        })
    rows.sort(key=lambda r: (r["liz"], r["p_kod"]))
    return {"Set_URDeviceMeters": rows}, zamech
