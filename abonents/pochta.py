"""Отправка документов абонентам по почте (auto_send_mail, proced.info_potreb_ma
старой программы).

Настройки — «Настройка рассылки писем» (smtp_nas): сервер, порт, отправитель,
тема, текст письма; пароль — TEPLO_SMTP_PASSWORD (иначе smtp_nas.password).
Текст письма, как в старой программе: <текст> <месяц> <год> года.

В отличие от старой программы ошибка одного письма не прерывает рассылку:
каждая попытка записывается в реестр (Pismo) с результатом, неотправленные
можно отправить повторно.
"""

import re
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.utils import timezone

from catalogs.models import Potreb, SmtpNas

from . import documents, pdf
from .models import Pismo

EMAIL = re.compile(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+")


def adresa(text):
    """Адреса из поля «e-mail» карты (может быть несколько через , или ;)."""
    return EMAIL.findall(text or "")


def nastrojki():
    return SmtpNas.objects.first()


def gotovo():
    """Текст причины, почему отправлять нельзя, или пустая строка."""
    s = nastrojki()
    if s is None or not (s.smtp or "").strip():
        return "Не заполнена «Настройка рассылки писем»: нет почтового сервера (smtp_nas)."
    if not (s.from_dbf or "").strip():
        return "В «Настройке рассылки писем» не указан адрес отправителя."
    return ""


def connection():
    s = nastrojki()
    port = s.port or 25
    ssl = bool(s.puses) and port == 465
    return get_connection(
        host=(s.smtp or "").strip(), port=port,
        username=(s.senduserna or "").strip() or None if s.paunt else None,
        password=(settings.TEPLO_SMTP_PASSWORD or (s.password or "").strip()) if s.paunt else None,
        use_ssl=ssl, use_tls=bool(s.puses) and not ssl, timeout=s.timeout or 30, fail_silently=False)


def poluchatel(dok):
    """Лицевой договора, на чей адрес отправлять: сначала абонент (категория
    абонента 1) с адресом, затем любой с адресом."""
    recs = dok.stroki
    for s in sorted(recs, key=lambda s: (s.p.id_katabon != 1, s.p.potreb_id)):
        if adresa(s.p.mail):
            return s.p
    return None


@dataclass
class Itog:
    dok: object
    pismo: Pismo


def otpravit(dok, vid, context, user="", conn=None):
    """Отправить один документ по договору. Возвращает запись реестра."""
    p = poluchatel(dok) or dok.glav
    to = adresa(p.mail)
    nomer = Pismo.sleduyushchij_nomer()
    pismo = Pismo(nomer=nomer, user=user, cod_gor=dok.gorod.cod_gorod, nom_dog=dok.nom_dog, potreb_id=p.potreb_id,
                  name_potre=(p.name_potre or "").strip()[:120], email=", ".join(to), vid=vid,
                  nom_mes=dok.mes, god=dok.god, status=Pismo.OSHIBKA)
    if not to:
        pismo.oshibka = "Нет адреса электронной почты в карте абонента"
        pismo.save()
        return pismo
    try:
        path = pdf.save(dok, vid, {**context, "nomer": nomer})
        pismo.fail = str(path)
        s = nastrojki()
        body = f"{(s.pismo or '').strip()} {dok.mes_im} {dok.god} года".strip()
        msg = EmailMessage(subject=(s.tema or "").strip() or pdf.VIDY[vid], body=body,
                           from_email=(s.from_dbf or "").strip(), to=to, connection=conn or connection())
        msg.attach(path.name, path.read_bytes(), "application/pdf")
        msg.send()
    except Exception as e:  # ошибка одного письма не прерывает рассылку
        pismo.oshibka = f"{type(e).__name__}: {e}"[:2000]
        pismo.save()
        return pismo
    pismo.status = Pismo.OK
    pismo.save()
    Potreb.objects.filter(cod_gor=dok.gorod.cod_gorod, nom_dog=dok.nom_dog).update(dataotpr=timezone.now())
    return pismo


def rassylka(cod_gor, nomera, vid, context, user="", mesyac=None):
    """Отправить документы по списку договоров участка одной SMTP-сессией."""
    out = []
    conn = connection()
    try:
        conn.open()
    except Exception:
        conn = None   # ошибка соединения запишется в каждую запись реестра
    try:
        for nom in nomera:
            dok = documents.sobrat(cod_gor, nom, mesyac=mesyac)
            if dok is not None:
                out.append(otpravit(dok, vid, context, user, conn))
    finally:
        if conn is not None:
            conn.close()
    return out


def spisok(cod_gor, mes, god, vid, mesyac=None, kanal=Pismo.POCHTA):
    """Договоры участка для рассылки за месяц: [(документ, получатель, отмечен
    по умолчанию, последняя запись реестра за месяц)]. По умолчанию отмечены
    договоры с признаком «Почта» в карте, которым документ ещё не отправлен."""
    last = {}
    for p in Pismo.objects.filter(cod_gor=cod_gor, nom_mes=mes, god=god, vid=vid, kanal=kanal).order_by("pk"):
        last[p.nom_dog] = p
    out = []
    for nom in documents.dogovory(cod_gor, mesyac=mesyac):
        dok = documents.sobrat(cod_gor, nom, mesyac=mesyac)
        if dok is None:
            continue
        zapis = last.get(nom)
        if kanal == Pismo.KREDO:
            from . import kredo_dok
            p = kredo_dok.poluchatel(dok)
            flag = bool(p and any(s.p.kredo_ras for s in dok.stroki))
        else:
            p = poluchatel(dok)
            flag = bool(p and any(s.p.mail_ras for s in dok.stroki))
        flag = flag and not (zapis and zapis.status == Pismo.OK)
        out.append((dok, p, flag, zapis))
    return out
