"""Данные закрытых месяцев для отчетов за период (форма arhiv старой
программы, которая читала файлы Arhiv\\PoMMГГГГ.dbf, DaMMГГГГ.dbf,
OtMMГГГГ.dbf).

Источник — архив месяца MesArhiv: месяцы, закрытые в новой программе, и
месяцы, загруженные из файлов старой программы (команда arhiv_import).
Если месяц есть в обоих, берется закрытый в новой программе.

Период задается месяцами по календарю (в старой программе число месяцев
считалось как (конец − начало) / 30 + 1 и на длинных периодах могло
ошибаться на месяц).
"""

from catalogs.models import Danrasch, Potreb

from .layout import RASCHET
from .models import MesArhiv

MES = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
       "сентябрь", "октябрь", "ноябрь", "декабрь"]


def mesyacy(nach, kon):
    """[(месяц, год)] от nach до kon включительно; nach, kon — (месяц, год)."""
    (m, g), out = nach, []
    while (g, m) <= (kon[1], kon[0]) and len(out) < 1200:
        out.append((m, g))
        m, g = (1, g + 1) if m == 12 else (m + 1, g)
    return out


def nazvanie(mes, god):
    return f"{MES[mes - 1]} {god}"


def zakrytye(spisok=None):
    """{(месяц, год): MesArhiv} — по месяцу одна запись: закрытая в новой
    программе важнее загруженной из старой, более поздняя важнее ранней."""
    qs = MesArhiv.objects.defer("data").order_by("pk")
    out = {}
    for a in qs:
        key = (a.nom_mes, a.god)
        if spisok is not None and key not in spisok:
            continue
        old = out.get(key)
        if old is None or not (old.istochnik == MesArhiv.WEB and a.istochnik != MesArhiv.WEB):
            out[key] = a
    return out


def poslednij():
    """(месяц, год) последнего закрытого месяца или None."""
    a = MesArhiv.objects.order_by("-god", "-nom_mes").defer("data").first()
    return (a.nom_mes, a.god) if a else None


def gody():
    return sorted(set(MesArhiv.objects.values_list("god", flat=True)), reverse=True)


def _objects(model, rows):
    """Несохраняемые объекты модели по строкам архива (лишние ключи — например,
    поля, которых нет в новой программе, — отбрасываются)."""
    fields = {f.attname: f for f in model._meta.concrete_fields}
    out = []
    for row in rows:
        kw = {}
        for k, v in row.items():
            f = fields.get(k)
            if f is not None:
                try:
                    kw[k] = f.to_python(v)
                except Exception:
                    kw[k] = None
        out.append(model(**kw))
    return out


class Mesyac:
    """Закрытый месяц: записи potreb и danrasch на момент закрытия."""

    def __init__(self, arh):
        self.arh = arh
        self.mes, self.god = arh.nom_mes, arh.god
        t = self.tables = arh.tables()
        self.potreb = _objects(Potreb, t.get("potreb", []))
        self.danrasch = _objects(Danrasch, t.get("danrasch", []))

    @property
    def nazvanie(self):
        return nazvanie(self.mes, self.god)

    def gorod(self, code):
        return next((d for d in self.danrasch if d.cod_gorod == code), None)

    def dejstvuyushchie(self, code=None):
        """Записи с заключённым/возобновлённым договором. В архивах до появления
        статуса договора (d_stat пуст у всех) — все записи."""
        recs = [p for p in self.potreb if code is None or p.cod_gor_id == code]
        if any(p.d_stat is not None for p in self.potreb):
            recs = [p for p in recs if p.d_stat in RASCHET]
        return recs

    def tarify(self, code):
        """{код: (тариф, тариф для дизеля)} участка на момент закрытия месяца или
        None, если тарифов в архиве нет. Как TarifGorod.dlya: общий tarif.dbf,
        поверх него — тарифы участка (их хранят месяцы, закрытые в новой программе)."""
        obshchie, uch = self.tables.get("tarif") or [], self.tables.get("tarif_gorod") or []
        if not obshchie and not uch:
            return None
        out = {}
        for row in obshchie:
            if row.get("id_tar") is not None:
                out[int(row["id_tar"])] = (row.get("zn_tar") or 0, row.get("diz_tar") or 0)
        for row in uch:
            if row.get("gorod") == code and row.get("id_tar") is not None:
                out[int(row["id_tar"])] = (row.get("zn_tar") or 0, row.get("diz_tar") or 0)
        return out or None

    def licevoj(self, potreb_id):
        return next((p for p in self.potreb if p.potreb_id == potreb_id), None)


def zagruzit(spisok):
    """[(месяц, год, Mesyac | None)] по списку месяцев; None — месяца нет в архиве."""
    arh = zakrytye(set(spisok))
    out = []
    for key in spisok:
        a = arh.get(key)
        out.append((key[0], key[1], Mesyac(MesArhiv.objects.get(pk=a.pk)) if a else None))
    return out


def najti(key):
    """Mesyac закрытого месяца key = (месяц, год) или None."""
    a = zakrytye({key}).get(key)
    return Mesyac(MesArhiv.objects.get(pk=a.pk)) if a else None


def vybor():
    """[("ГГГГ-ММ", «месяц год»)] закрытых месяцев, новые первыми."""
    return [(f"{g}-{m:02d}", nazvanie(m, g)) for m, g in sorted(zakrytye(), key=lambda k: (k[1], k[0]), reverse=True)]
