"""Передача в АПК «КРЭДО» данных об абонентах, договорах и точках потребления.

Повторяет кнопку «Передать данные договора в КРЭДО» карты абонента
(karta.Page3.Command12) и регистрацию абонентов участка (apk_kredo.prg,
кнопка Command3 формы rric):

- Set_URAbon  — информация об абонентах (каждая запись potreb);
- Set_URDogv  — информация о договорах (только абоненты, id_katabon = 1);
- Set_URPotr  — объекты (точки) потребления (каждая запись potreb).

Пакет — таблица в XML, как CURSORTOXML(…, 1, 16, 0) старой программы с
корнем <root>; в процедуру он передаётся параметром @xmlData={base64}…,
закодированный методом ToBase64 того же COM-объекта RRIC_COM_OBJECT.Invoker.
Строки отправляются порциями до 1000 (в старой программе — только первые 1000).

Длина полей — как в таблицах Set_UR* старой программы (VFP обрезал значения
по ширине поля, так их КРЭДО и получал): например, тип договора уходит как
«Юрлица Теп».
"""

import datetime
from xml.sax.saxutils import escape

from catalogs.models import Potreb

from . import kredo

PORCIYA = 1000
TIP_DOGOVORA = "Юрлица Тепло"
NE_OBJEKTY = ("-----", "Абонентское население")

# Поля пакетов: (поле, ширина в таблице старой программы; None — число или дата).
POLYA = {
    "Set_URAbon": (("liz", 10), ("a_type", None), ("a_name_short", 200), ("a_name_full", 240),
                   ("ao_code", 31), ("house", 10), ("flat", 10), ("ru_name", 20), ("ru_phone", 10),
                   ("fiscode", 10), ("account", 10), ("rs", 25), ("bank", 50)),
    "Set_URDogv": (("liz", 10), ("tip", 10), ("n_dog", 10), ("d_dog", None), ("dn_dog", None),
                   ("dk_dog", None), ("d_stat", None)),
    "Set_URPotr": (("liz", 10), ("p_kod", 10), ("p_name", 250), ("ao_code", 32), ("house", 10),
                   ("flat", 10), ("stat", None)),
}
NAZVANIYA = {
    "Set_URAbon": "Абоненты",
    "Set_URDogv": "Договоры",
    "Set_URPotr": "Точки потребления",
}


def _s(v):
    return ("" if v is None else str(v)).strip()


def kod6(n):
    """Шестизначный код с нулями: substr(str(n+1000000,7),2,6)."""
    return f"{int(n or 0) % 1000000:06d}"


def objekt(p):
    """Запись участвует в регистрации: есть название объекта (apk_kredo.prg)."""
    name = _s(p.nameobakt)
    return bool(name) and name not in NE_OBJEKTY


def golovnoj(zapisi):
    """Лицевой головного абонента договора: первая запись с d_stat = 60 и
    id_katabon = 1 (apk_kredo.prg), иначе первая с id_katabon = 1."""
    zapisi = sorted(zapisi, key=lambda p: p.potreb_id)
    for usl in (lambda p: p.d_stat == 60 and p.id_katabon == 1, lambda p: p.id_katabon == 1):
        for p in zapisi:
            if usl(p):
                return kod6(p.potreb_id)
    return None


def stroki(zapisi):
    """Строки трёх пакетов по записям potreb и замечания к ним.
    Возвращает ({процедура: [строка]}, [замечание])."""
    paket = {k: [] for k in POLYA}
    zamech = []
    po_dog = {}
    for p in zapisi:
        po_dog.setdefault((p.cod_gor_id, p.nom_dog), []).append(p)
    glav = {k: golovnoj(v) for k, v in po_dog.items()}
    for p in sorted(zapisi, key=lambda p: (p.nom_dog or 0, p.potreb_id)):
        liz = kod6(p.potreb_id)
        paket["Set_URAbon"].append({
            "liz": liz, "a_type": p.a_type, "a_name_short": _s(p.name_potre), "a_name_full": _s(p.name_potre),
            "ao_code": _s(p.ao_code), "house": _s(p.ura_dom), "flat": _s(p.ura_kv), "ru_name": _s(p.direktor),
            "ru_phone": _s(p.telefon), "fiscode": _s(p.fisk_cod), "account": str(p.potreb_id),
            "rs": _s(p.ras_chet), "bank": _s(p.name_banka),
        })
        if p.id_katabon == 1:
            if p.data_dog is None:
                zamech.append(f"Л/с {p.potreb_id}: нет даты договора — договор не передаётся")
            else:
                paket["Set_URDogv"].append({
                    "liz": liz, "tip": TIP_DOGOVORA, "n_dog": kod6(p.nom_dog), "d_dog": p.data_dog,
                    "dn_dog": p.dn_dog, "dk_dog": p.dk_dog, "d_stat": p.d_stat,
                })
        glavnyj = _s(p.liz) or glav.get((p.cod_gor_id, p.nom_dog))
        if not glavnyj:
            zamech.append(f"Л/с {p.potreb_id}: у договора № {p.nom_dog} нет головного абонента — "
                          f"точка потребления передаётся со своим лицевым")
            glavnyj = liz
        paket["Set_URPotr"].append({
            "liz": glavnyj, "p_kod": liz, "p_name": _s(p.nameobakt), "ao_code": _s(p.ao_code),
            "house": _s(p.oba_dom), "flat": _s(p.oba_kv), "stat": 1 if p.d_stat == 60 else 0,
        })
        if not _s(p.ao_code):
            zamech.append(f"Л/с {p.potreb_id}: не заполнен код адреса КЛАДР (ao_code)")
    return paket, zamech


def _znach(v, shirina):
    if v is None:
        return ""
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime("%Y-%m-%d")
    v = str(v).strip()
    return v[:shirina] if shirina else v


def kolonki(proc, r):
    """Значения строки в том виде, в каком они уйдут в пакет (даты — датами)."""
    return [r.get(f) if not shirina or r.get(f) is None else str(r.get(f)).strip()[:shirina]
            for f, shirina in POLYA[proc]]


def xml_paketa(proc, rows):
    """Таблица в XML, как CURSORTOXML('row','xml',1,16,0) с заменой VFPData на root."""
    out = ['<?xml version = "1.0" encoding="Windows-1251" standalone="yes"?>', "<root>"]
    for r in rows:
        out.append("\t<row>")
        for pole, shirina in POLYA[proc]:
            v = _znach(r.get(pole), shirina)
            out.append(f"\t\t<{pole}>{escape(v)}</{pole}>" if v != "" else f"\t\t<{pole}/>")
        out.append("\t</row>")
    out.append("</root>")
    return "\n".join(out) + "\n"


def _bez_povtorov(rows):
    """SELECT DISTINCT: одинаковые строки — один раз."""
    vidal, out = set(), []
    for r in rows:
        k = tuple(sorted((k, str(v)) for k, v in r.items()))
        if k not in vidal:
            vidal.add(k)
            out.append(r)
    return out


def porcii(proc, rows):
    """XML пакетов процедуры по PORCIYA строк."""
    rows = _bez_povtorov(rows)
    return [xml_paketa(proc, rows[i:i + PORCIYA]) for i in range(0, len(rows), PORCIYA)]


def zapisi_dogovora(p):
    """Записи договора, к которому относится лицевой: с названием объекта, как
    при регистрации участка, и сам лицевой (его передавала кнопка карты)."""
    if not p.nom_dog:
        return [p]
    qs = Potreb.objects.filter(cod_gor=p.cod_gor_id, nom_dog=p.nom_dog).order_by("potreb_id")
    return [x for x in qs if objekt(x) or x.pk == p.pk]


def zapisi_uchastka(cod_gor):
    return [p for p in Potreb.objects.filter(cod_gor=cod_gor).order_by("nom_dog", "potreb_id") if objekt(p)]


def ret_val(otvet):
    """Ответ сервера (поле ret_val), как «Ответ сервера РРиЦ - …» в старой программе."""
    from .kredo_kody import tablica
    try:
        return "; ".join(r["ret_val"] for r in tablica(otvet, "ret_val") if r.get("ret_val"))
    except kredo.KredoError:
        return ""


def peredat(cod_gor, zapisi, user="", nom_dog=None, proverka=False, invoker=None):
    """Передать в КРЭДО абонентов, договоры и точки потребления записей
    (при proverka — только собрать пакеты). Возвращает запись журнала
    KredoPeredacha. Ошибка сервиса останавливает передачу."""
    from .models import KredoPeredacha
    paket, zamech = stroki(zapisi)
    z = KredoPeredacha(user=user[:150], cod_gor=cod_gor, nom_dog=nom_dog, proverka=proverka,
                       abon=len(paket["Set_URAbon"]), dogv=len(paket["Set_URDogv"]),
                       potr=len(paket["Set_URPotr"]), zamechaniya="\n".join(zamech))
    xmls, otvety = [], []
    try:
        comorg = kredo.nastrojki(cod_gor)["comorg"]
        inv = None
        for proc in POLYA:
            for x in porcii(proc, paket[proc]):
                xmls.append(f"<!-- {proc} -->\n{x}")
                if proverka:
                    continue
                inv = inv or invoker or kredo.ComInvoker(cod_gor)
                otvet = kredo.proverit(inv.exec_proc(proc, f"@comorg_id={comorg}", xml=x))
                otvety.append(f"{proc}: {ret_val(otvet) or otvet.strip()[:500]}")
    except Exception as e:
        z.status = KredoPeredacha.OSHIBKA
        z.oshibka = (str(e) if isinstance(e, kredo.KredoError) else f"{type(e).__name__}: {e}")[:2000]
    else:
        z.status = KredoPeredacha.PROVERKA if proverka else KredoPeredacha.OK
    z.xml = "\n".join(xmls)
    z.otvet = "\n".join(otvety)[:4000]
    z.save()
    return z
