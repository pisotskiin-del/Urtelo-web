"""Коды абонентов в АПК «КРЭДО»: организация (org_in) и представитель (pid_in).

Повторяет форму kredo старой программы:
- список юрлиц и ИП, зарегистрированных в КРЭДО (Kredo_MainOrgs,
  Kredo_MainIndividuals), сохраняется в программе (KredoOrg);
- организация абонента находится по фискальному коду или лицевому № в КРЭДО
  (rric_acn), либо выбирается по названию;
- представители выбранной организации — процедура Kredo_Users;
- в карту записываются org_in, pid_in, rric_acn, Ф.И.О. и должность представителя.
"""

import re
import xml.etree.ElementTree as ET

from django.db import transaction
from django.db.models import Q

from catalogs.models import Potreb

from . import kredo


def _local(tag):
    return tag.rsplit("}", 1)[-1].lower()


def tablica(xml, klyuch):
    """Строки таблицы ответа КРЭДО: [{поле: текст}] — элементы, у которых
    есть дочерний элемент klyuch (регистр и пространства имён не важны)."""
    try:
        text = re.sub(r"^\s*<\?xml[^>]*\?>", "", xml or "")
        root = ET.fromstring(text.strip().encode("utf-8"))
    except ET.ParseError as e:
        raise kredo.KredoError(f"Ответ КРЭДО — не XML: {e}") from e
    out = []
    for el in root.iter():
        if _local(el.tag) == "schema":
            continue
        vals = {_local(ch.tag): (ch.text or "").strip() for ch in el if len(ch) == 0}
        if klyuch in vals:
            out.append(vals)
    return out


def _fisk(v):
    return re.sub(r"\D", "", v or "")


def obnovit_organizacii(cod_gor, invoker=None):
    """Загрузить из КРЭДО список юрлиц и ИП. Возвращает их число."""
    from .models import KredoOrg
    inv = invoker or kredo.ComInvoker(cod_gor)
    novye = []
    for proc, ip in (("Kredo_MainOrgs", False), ("Kredo_MainIndividuals", True)):
        for r in tablica(kredo.proverit(inv.exec_proc(proc, "@start_date=null")), "org_id"):
            if not r.get("org_id"):
                continue
            novye.append(KredoOrg(org_id=r["org_id"], s_name=(r.get("s_name") or r.get("f_name") or "")[:250],
                                  rric_acn=(r.get("rric_acn") or "")[:10], fiscode=_fisk(r.get("fiscode"))[:20],
                                  adr_full=(r.get("adr_full") or "")[:250], ip=ip))
    if not novye:
        raise kredo.KredoError("КРЭДО не вернул ни одной организации")
    with transaction.atomic():
        KredoOrg.objects.all().delete()
        KredoOrg.objects.bulk_create(novye)
    return len(novye)


def najti(p):
    """Организации КРЭДО, подходящие абоненту: по лицевому № в КРЭДО и по
    фискальному коду."""
    from .models import KredoOrg
    usl = Q(pk__in=[])
    if (p.rric_acn or "").strip():
        usl |= Q(rric_acn=p.rric_acn.strip())
    if _fisk(p.fisk_cod):
        usl |= Q(fiscode=_fisk(p.fisk_cod))
    if (p.org_in or "").strip():
        usl |= Q(org_id__iexact=p.org_in.strip())
    return list(KredoOrg.objects.filter(usl))


def predstaviteli(cod_gor, org_id, invoker=None):
    """Представители организации в КРЭДО: [{pid, fio, pos_name, ...}]."""
    if not re.fullmatch(r"[0-9A-Fa-f-]{36}", org_id or ""):
        raise kredo.KredoError("Неверный код организации КРЭДО")
    inv = invoker or kredo.ComInvoker(cod_gor)
    out = []
    for r in tablica(kredo.proverit(inv.exec_proc("Kredo_Users", f"@org_id={org_id},@pid=null")), "pid"):
        if r.get("pid"):
            r["fio"] = fio(r)
            out.append(r)
    return out


def fio(r):
    """«И.О.Фамилия», как в старой программе."""
    i, o, f = (r.get("f_name") or "").strip(), (r.get("m_name") or "").strip(), (r.get("l_name") or "").strip()
    return f"{i[:1]}.{o[:1]}.{f}" if i else f


def zapisat(p, org, predst):
    """Записать коды КРЭДО в карту лицевого."""
    p = Potreb.objects.get(pk=p.pk)
    p.org_in = org.org_id
    p.rric_acn = org.rric_acn or p.rric_acn
    p.pid_in = predst["pid"] if predst else ""
    p.users_name = (predst["fio"] if predst else "")[:100]
    p.pos_name = (predst.get("pos_name") or "" if predst else "")[:200]
    p.save(update_fields=["org_in", "rric_acn", "pid_in", "users_name", "pos_name"])
    return p


def ochistit(p):
    Potreb.objects.filter(pk=p.pk).update(org_in="", pid_in="", users_name="", pos_name="")
