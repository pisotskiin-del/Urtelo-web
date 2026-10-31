"""Обмен с АПК «КРЭДО» (РРИЦ): приём показаний приборов учёта.

Повторяет кнопки формы rric старой программы:
- «Прием информации о последних показаниях приборов учета абонентов»
  (Command16): процедура Kredo_DeviceMeters_Info за текущий месяц участка;
- «Разнести последние показания счетчиков по лицевым счетам» (Command36):
  показание (cur_pok) и дата (date_pok) записываются в карту лицевого
  (potreb.pok_new, potreb.date_pok); если новое показание меньше того, что
  уже в карте, — только после подтверждения.

Вызов идёт через COM-объект РРИЦ RRIC_COM_OBJECT.Invoker (pywin32, только
Windows). Сертификат клиента ищется в хранилище «Личные» пользователя
Windows, под которым работает программа.
"""

import contextlib
import datetime
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.conf import settings

from catalogs.models import Potreb

# Участок: код организации в КРЭДО (comorg) и сертификат клиента по умолчанию.
# Имя и отпечаток сертификата меняются в «Справочники → Настройки программы».
UCHASTKI = {
    1: {"comorg": 210, "cert": "TTE_Ryb"},
    2: {"comorg": 211, "cert": "TTE_Dub"},
    3: {"comorg": 212, "cert": "TTE_Kam"},
}

POK_MAX = Decimal("999999.999")   # potreb.pok_new: N(9,3)


class KredoError(Exception):
    pass


def nastrojki(cod_gor):
    u = UCHASTKI.get(cod_gor)
    if u is None:
        raise KredoError(f"Для участка {cod_gor} не задан код организации в КРЭДО")
    from abonents.models import Nastroika
    n = Nastroika.kredo(cod_gor)
    thumb = n["thumb"] or (getattr(settings, "TEPLO_KREDO_THUMB", {}) or {}).get(cod_gor, "")
    thumb = re.sub(r"[^0-9a-fA-F]", "", thumb or "").lower()
    return {**u, "cert": n["cert"] or u["cert"], "thumb": thumb, "endpoint": settings.TEPLO_KREDO_ENDPOINT,
            "service": settings.TEPLO_KREDO_SERVICE_CERT}


def period(mes, god):
    """Первый и последний день месяца в виде дд.мм.гггг, как в старой программе."""
    nach = datetime.date(god, mes, 1)
    kon = (nach + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    return nach.strftime("%d.%m.%Y"), kon.strftime("%d.%m.%Y")


class ComInvoker:
    """Вызов процедур КРЭДО через RRIC_COM_OBJECT.Invoker."""

    def __init__(self, cod_gor):
        self.n = nastrojki(cod_gor)

    def exec_proc(self, name, params):
        try:
            import pythoncom
            import win32com.client
        except ImportError:
            raise KredoError("Нет модуля pywin32: обмен с КРЭДО работает только в Windows "
                             "(python -m pip install pywin32)") from None
        pythoncom.CoInitialize()   # каждый запрос Django — в своём потоке
        try:
            try:
                x = win32com.client.Dispatch("RRIC_COM_OBJECT.Invoker")
            except Exception as e:
                raise KredoError(f"Не удалось создать RRIC_COM_OBJECT.Invoker: {e}") from e
            x.ClientCertName = self.n["cert"]
            if self.n["thumb"]:
                x.ClientCertThumb = self.n["thumb"]
            x.ServiceCertName = self.n["service"]
            x.EndpointUrl = self.n["endpoint"]
            x.MaxMessageSize = 1000000000
            # Метод без аргументов при позднем связывании читается как свойство:
            # со скобками pywin32 вызвал бы ToString() результата.
            c = x.CreateChannel
            if c is None or isinstance(c, str):
                raise KredoError(f"Не удалось открыть канал связи с РРИЦ: {c or x.GetLastError}")
            try:
                return str(x.ExecProc(c, name, params) or "")
            finally:
                with contextlib.suppress(Exception):   # канал закрывается сервером сам
                    x.CloseChannel(c)
        except KredoError:
            raise
        except Exception as e:
            raise KredoError(f"Ошибка вызова {name}: {e}") from e
        finally:
            pythoncom.CoUninitialize()


def proverit(otvet):
    """Текст ошибки из ответа сервиса (<error>…</error>) — исключением."""
    m = re.search(r"<error>(.*?)</error>", otvet or "", re.DOTALL)
    if m:
        raise KredoError(m.group(1).strip() or "Сервис РРИЦ вернул ошибку")
    return otvet


def zaprosit_pokazaniya(cod_gor, mes, god, invoker=None):
    """XML с показаниями приборов абонентов участка за месяц."""
    comorg = nastrojki(cod_gor)["comorg"]
    nach, kon = period(mes, god)
    inv = invoker or ComInvoker(cod_gor)
    return proverit(inv.exec_proc("Kredo_DeviceMeters_Info",
                                  f"@comorg={comorg},@org_id=null,@start_date={nach},@end_date={kon}"))


# --- разбор ответа ----------------------------------------------------------

POLYA = ("p_kod", "d_num", "prev_pok", "cur_pok", "waitable", "date_pok")


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _chislo(v):
    v = (v or "").strip().replace(",", ".").replace(" ", "")
    if not v:
        return None
    try:
        return Decimal(v)
    except InvalidOperation:
        return None


def _data(v):
    v = (v or "").strip()
    for fmt, n in (("%Y-%m-%d", 10), ("%d.%m.%Y", 10), ("%Y%m%d", 8)):
        try:
            return datetime.datetime.strptime(v[:n], fmt).date()
        except ValueError:
            pass
    return None


def razobrat(xml):
    """Строки ответа: [{p_kod, d_num, prev_pok, cur_pok, waitable, date_pok}].

    Принимает таблицу в любом из видов, которые понимал XMLTOCURSOR: строка —
    элемент с дочерними элементами (или атрибутами) p_kod, cur_pok, …;
    регистр и пространства имён не важны, схема (xs:schema) пропускается.
    """
    try:
        # Объявление <?xml … encoding=…?> убирается: текст уже раскодирован.
        text = re.sub(r"^\s*<\?xml[^>]*\?>", "", xml or "")
        root = ET.fromstring(text.strip().encode("utf-8"))
    except ET.ParseError as e:
        raise KredoError(f"Ответ КРЭДО — не XML: {e}") from e
    out = []
    for el in root.iter():
        if _local(el.tag) == "schema":
            continue
        vals = {_local(ch.tag): (ch.text or "") for ch in el}
        vals.update({k.lower(): v for k, v in el.attrib.items() if _local(k) in POLYA})
        if "p_kod" not in vals or "cur_pok" not in vals:
            continue
        out.append({
            "p_kod": (vals.get("p_kod") or "").strip(),
            "d_num": (vals.get("d_num") or "").strip(),
            "prev_pok": _chislo(vals.get("prev_pok")),
            "cur_pok": _chislo(vals.get("cur_pok")),
            "waitable": _chislo(vals.get("waitable")),
            "date_pok": _data(vals.get("date_pok")),
        })
    return out


# --- сверка с картами и разнос ---------------------------------------------

NET, RAVNO, NOVOE, MENSHE, OSHIBKA = "net", "ravno", "novoe", "menshe", "oshibka"
STATUSY = {
    NET: "нет такого лицевого",
    RAVNO: "уже в карте",
    NOVOE: "новое показание",
    MENSHE: "меньше показания в карте",
    OSHIBKA: "не число",
}


@dataclass
class Stroka:
    nomer: int              # номер строки ответа
    r: dict
    p: Potreb = None
    status: str = NET
    dubl: bool = False      # на лицевой пришло несколько показаний
    posled: bool = False    # из них последнее по дате (один прибор)

    @property
    def potreb_id(self):
        try:
            return int(Decimal(self.r["p_kod"]))
        except (InvalidOperation, ValueError):
            return None

    @property
    def rashod(self):
        cur, prev = self.r["cur_pok"], self.r["prev_pok"]
        return cur - prev if cur is not None and prev is not None else None

    @property
    def status_text(self):
        return STATUSY[self.status]

    @property
    def mozhno(self):
        return self.status in (NOVOE, MENSHE, RAVNO)

    @property
    def otmetit(self):
        """Отмечать ли по умолчанию: новое показание не меньше старого и
        единственное (или последнее) на лицевой. Меньшее — только по подтверждению."""
        return self.status == NOVOE and (not self.dubl or self.posled)


def _r2(v):
    return Decimal(v or 0).quantize(Decimal("0.01"))


def sverit(rows):
    """Строки ответа рядом с картами лицевых.

    КРЭДО повторяет одно и то же показание в нескольких строках (по одной на
    документ) — повторы убираются. Если на лицевой пришло несколько разных
    показаний одного прибора, по умолчанию отмечается последнее по дате; если
    приборов несколько — ни одно (в карте одно показание отопления).
    """
    vidal, stroki = set(), []
    for r in rows:
        key = (r["p_kod"], r["d_num"], r["cur_pok"], r["date_pok"])
        if key not in vidal:
            vidal.add(key)
            stroki.append(Stroka(nomer=len(stroki), r=r))
    ids = {s.potreb_id for s in stroki if s.potreb_id is not None}
    karty = {p.potreb_id: p for p in Potreb.objects.filter(potreb_id__in=ids).select_related("cod_gor")}
    gruppy = defaultdict(list)
    for s in stroki:
        gruppy[s.potreb_id].append(s)
    for s in stroki:
        s.p = karty.get(s.potreb_id)
        g = gruppy[s.potreb_id]
        if s.p is not None and len(g) > 1:
            s.dubl = True
            if len({x.r["d_num"] for x in g}) == 1:
                s.posled = s is max(g, key=lambda x: (x.r["date_pok"] or datetime.date.min, x.r["cur_pok"] or 0))
        cur = s.r["cur_pok"]
        if s.p is None:
            s.status = NET
        elif cur is None or cur < 0 or cur > POK_MAX:
            s.status = OSHIBKA
        elif _r2(s.p.pok_new) > cur:      # старая программа: ROUND(pok_new,2) <= cur_pok
            s.status = MENSHE
        elif _r2(s.p.pok_new) == _r2(cur) and s.p.date_pok == s.r["date_pok"]:
            s.status = RAVNO
        else:
            s.status = NOVOE
    return stroki


def raznesti(stroki, nomera):
    """Записать в карты показания отмеченных строк. Возвращает список
    изменений [[л/№, было, стало, дата было, дата стало]]."""
    izm = []
    for s in stroki:
        if s.nomer not in nomera or not s.mozhno:
            continue
        p = Potreb.objects.get(pk=s.p.pk)
        cur = s.r["cur_pok"]
        izm.append([p.potreb_id, str(p.pok_new) if p.pok_new is not None else None, str(cur),
                    p.date_pok.isoformat() if p.date_pok else None,
                    s.r["date_pok"].isoformat() if s.r["date_pok"] else None])
        p.pok_new = cur
        if s.r["date_pok"]:
            p.date_pok = s.r["date_pok"]
        p.save(update_fields=["pok_new", "date_pok"])
    return izm
