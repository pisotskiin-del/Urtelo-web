"""Отправка подписанной «Информации-счёта» абоненту через АПК «КРЭДО».

Повторяет infch_kredo_kr старой программы (кнопка «Отправка по системе
КРЭДО» в карте, при заполненных в карте org_in и pid_in):

1. PDF «Информации-счёта» (тот же, что для почты);
2. электронный документ крипто-модуля RRIC_COM_OBJECT.Crypto: реквизиты
   предприятия, рег. номер 07/<номер в реестре>, получатель, подписант,
   исполнитель, логотип, вложение — PDF;
3. подпись сертификатом участка из хранилища «Личные» пользователя Windows,
   со штампом времени (TEPLO_KREDO_TSA), проверка подписи;
4. копия подписанного документа — XML рядом с PDF;
5. сжатие и запись в КРЭДО процедурой Set_URDocument (@type=3, отправитель
   org_out/pid_out участка, получатель org_in/pid_in из карты).

Режим проверки (proverka=True) выполняет шаги 1–4 без отправки.
Каждая попытка записывается в реестр писем (Pismo, канал «КРЭДО»).
"""

import base64
import contextlib
import re
from pathlib import Path

from django.conf import settings

from . import kredo, pdf
from .models import Pismo

# Реквизиты предприятия в электронном документе (infch_kredo_kr).
REKVIZITY = {
    "namemd": 'МИНИСТЕРУЛ  ДЕЗВОЛТЭРИЙ ЕКОНОМИЧЕ  АЛ РМН ЫНТРЕПРИНДЕРЯ  УНИТАРЭ  ДЕ  СТАТ  РАЙОНАЛЭ "ТИРАСТЕПЛОЭНЕРГО"',
    "nameukr": 'МIНIСТЕРСТВО ЕКОНОМIЧНОГО РОЗВИТКУ ПМР МIЖРАЙОННЕ  ДЕРЖАВНЕ УНIТАРНЕ  ПIДПРИЄМСТВО "ТIРАСТЕПЛОЕНЕРГIЯ"',
    "namemainru": "МИНИСТЕРСТВО ЭКОНОМИЧЕСКОГО РАЗВИТИЯ ПМР",
    "nameru": 'Межрайонное государственное унитарное предприятие "Тирастеплоэнерго"',
    "postaladdress": "ПМР,г.Тирасполь,ул.Шутова,д.3",
    # Вложенные поля документа задаются путём «раздел/поле»: просто «bankaccount»,
    # «datareg», «executorname» крипто-модуль не находит и оставляет пустыми.
    "referencedataorg/bankaccount": "2211290000000026",
    "referencedataorg/emailaddress": "tiraste@mail.ru",
    "nameviewdoc": "Информация-счет",
}
# Адрес участка (referencedataorg/postaladdress).
ADRES_UCHASTKA = {1: "г.Рыбница,  ул.Маяковского 43"}
# Подписант и исполнитель, если они не заданы в «Подписантах документов».
PODPISANT = ("Ведущий специалист СУиРТЭ г.Рыбница", "С.В.Борсуковский")
ISPOLNITEL = ("исп. В.М.Мельник", "555 32671")
STATUSY = {"Clean": 1, "Filled": 2, "Signed": 3, "Crypted": 4, "Compressed": 5}
LOGO = Path(__file__).with_name("data") / "kredo_logo.png"


def otpravitel(cod_gor):
    """GUID организации и представителя-отправителя участка в КРЭДО."""
    from .models import Nastroika
    n = Nastroika.kredo(cod_gor)
    o = (getattr(settings, "TEPLO_KREDO_OTPRAVITEL", {}) or {}).get(cod_gor) or {}
    org, pid = n["org"] or o.get("org"), n["pid"] or o.get("pid")
    if not org or not pid:
        raise kredo.KredoError(f"Для участка {cod_gor} не задан отправитель в КРЭДО: заполните коды "
                               f"org_out и pid_out в «Справочники → Настройки программы»")
    return org, pid


def poluchatel(dok):
    """Лицевой договора с кодами организации и представителя в КРЭДО (org_in,
    pid_in): сначала абонент (категория абонента 1), затем любой."""
    for s in sorted(dok.stroki, key=lambda s: (s.p.id_katabon != 1, s.p.potreb_id)):
        if (s.p.org_in or "").strip() and (s.p.pid_in or "").strip():
            return s.p
    return None


def _podpisi(dok):
    from .models import Podpisant
    dolj, fio = Podpisant.get(Podpisant.VED_SPEC, dok.gorod)
    _, isp = Podpisant.get(Podpisant.ISPOLNITEL, dok.gorod)
    podp = (dolj, fio) if fio else PODPISANT
    ispoln = (f"исп. {isp}" if isp else ISPOLNITEL[0], ISPOLNITEL[1])
    return podp, ispoln


class ComCrypto:
    """Подпись документа через RRIC_COM_OBJECT.Crypto (pywin32)."""

    @contextlib.contextmanager
    def objekt(self):
        kredo.razresheno()
        try:
            import pythoncom
            import win32com.client
        except ImportError:
            raise kredo.KredoError("Нет модуля pywin32: обмен с КРЭДО работает только в Windows") from None
        pythoncom.CoInitialize()
        try:
            try:
                yield win32com.client.Dispatch("RRIC_COM_OBJECT.Crypto")
            except kredo.KredoError:
                raise
            except Exception as e:
                raise kredo.KredoError(f"Ошибка крипто-модуля РРИЦ: {e}") from e
        finally:
            pythoncom.CoUninitialize()


def podpisat(x, spec):
    """Создать, подписать и сжать документ объектом крипто-модуля x.
    Возвращает (xml подписанного документа, base64 сжатого, статус, сертификат)."""
    # Методы без аргументов (CreateDocument, GetLastError) при позднем
    # связывании pywin32 читаются как свойства — без скобок.
    y = x.CreateDocument
    if not y or not isinstance(y, str):
        raise kredo.KredoError(f"Крипто-модуль не создал документ: {x.GetLastError}")
    for k, v in spec["info"].items():
        x.SetDocInfoParameter(y, k, v)
    x.AddRecipient(y, *spec["poluchatel"], "")
    x.AddSigner(y, *spec["podpisant"])
    x.SetDocInfoParameter(y, "executor/executorname", spec["ispolnitel"][0])
    x.SetDocInfoParameter(y, "executor/executorphone", spec["ispolnitel"][1])
    if spec.get("logo"):
        x.SetDocInfoLogo(y, spec["logo"])
    x.AddAttachment1(y, spec["vlozhenie"])
    # Крипто-модуль сам показывает окно выбора сертификата из хранилища «Личные»
    # (как в старой программе): выбрать сертификат заранее по отпечатку нельзя.
    s = x.SignDocument1(y, "CurrentUser", "My", 4, spec["tsa"])
    if not s:
        raise kredo.KredoError(f"Документ не подписан: {x.GetLastError or 'нет описания ошибки'}")
    sertifikat = proverit_sertifikat(str(x.CertificateInfo1(y, s) or ""), spec.get("thumb", ""))
    proverka = x.ValidateSignature(y, s)
    xml = str(x.GetDocumentContent(y) or "")
    x.CompressDocument(y)
    status = STATUSY.get(str(x.GetDocumentStatus(y)), 0)
    b64 = str(x.ConvertToBase64String(x.GetDocumentContent(y)) or "")
    return xml, b64, status, sertifikat


def _pole(xml, tag):
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xml or "", re.DOTALL)
    return m.group(1).strip() if m else ""


def proverit_sertifikat(info, thumb):
    """Документ должен быть подписан сертификатом участка (отпечаток из
    «Настройки программы»): в окне выбора легко ошибиться строкой."""
    cn = re.search(r"CN=([^,]+)", _pole(info, "subject"))
    imya = cn.group(1).strip() if cn else _pole(info, "subject")
    if not thumb:
        return imya
    vybran = re.sub(r"[^0-9a-f]", "", _pole(info, "thumbprint").lower())
    if vybran != re.sub(r"[^0-9a-f]", "", thumb.lower()):
        kto = _pole(info, "subject") or "неизвестный сертификат"
        raise kredo.KredoError(f"Документ подписан не сертификатом участка ({kto}). "
                               f"Выберите в окне сертификат участка; документ не отправлен")
    return imya


def spec_dokumenta(dok, p, nomer, pdf_path):
    from datetime import date
    podp, ispoln = _podpisi(dok)
    info = dict(REKVIZITY)
    info["referencedataorg/postaladdress"] = ADRES_UCHASTKA.get(dok.gorod.cod_gorod) or \
        f"г.{(dok.gorod.name_gorod or '').strip()}"
    info.update({"reg/datareg": date.today().strftime("%d.%m.%Y"), "reg/regnumber": f"07/{nomer}",
                 "reg/vhodregnumber": "", "reg/vhodregdate": "", "content": ""})
    logo = base64.b64encode(LOGO.read_bytes()).decode() if LOGO.exists() else ""
    return {
        "info": info,
        # Получатель: организация, должность и ФИО представителя, зарегистрированного
        # в КРЭДО (в старой программе — из Kredo_Users_all по pid_in); если их нет — из карты.
        "poluchatel": ((p.name_potre or "").strip(),
                       (p.pos_name or p.doljn_podp or "").strip(),
                       (p.users_name or p.direktor or "").strip()),
        "podpisant": podp, "ispolnitel": ispoln, "logo": logo,
        "vlozhenie": str(pdf_path), "tsa": settings.TEPLO_KREDO_TSA,
        "thumb": kredo.nastrojki(dok.gorod.cod_gorod)["thumb"],
    }


def otpravit(dok, context, user="", proverka=False, crypto=None, invoker=None):
    """Подписать «Информацию-счёт» по договору и отправить в КРЭДО (или, при
    proverka, только подписать). Возвращает запись реестра."""
    p = poluchatel(dok)
    glav = p or dok.glav
    nomer = Pismo.sleduyushchij_nomer()
    pismo = Pismo(nomer=nomer, user=user, kanal=Pismo.KREDO, cod_gor=dok.gorod.cod_gorod, nom_dog=dok.nom_dog,
                  potreb_id=glav.potreb_id, name_potre=(glav.name_potre or "").strip()[:120],
                  email=(f"{glav.org_in.strip()} / {glav.pid_in.strip()}" if p else ""),
                  vid="schet", nom_mes=dok.mes, god=dok.god, status=Pismo.OSHIBKA)
    if p is None:
        pismo.oshibka = "В карте нет кодов организации и представителя в КРЭДО (org_in, pid_in)"
        pismo.save()
        return pismo
    try:
        org_out, pid_out = otpravitel(dok.gorod.cod_gorod)
        path = pdf.save(dok, "schet", {**context, "nomer": nomer})
        pismo.fail = str(path)
        spec = spec_dokumenta(dok, p, nomer, path)
        with (crypto or ComCrypto()).objekt() as x:
            xml, b64, status, sertifikat = podpisat(x, spec)
        path.with_suffix(".xml").write_text(xml, encoding="utf-8")
        if proverka:
            pismo.oshibka = f"Проверка: документ подписан сертификатом {sertifikat}, XML сохранён ({path.with_suffix('.xml').name}), не отправлялся"
            pismo.status = Pismo.PROVERKA
            pismo.save()
            return pismo
        params = (f"@type=3,@org_out={org_out},@pid_out={pid_out},@org_in={p.org_in.strip()},"
                  f"@pid_in={p.pid_in.strip()},@doc_stat={status},@doc_data={{base64}}{b64}")
        otvet = kredo.proverit((invoker or kredo.ComInvoker(dok.gorod.cod_gorod)).exec_proc("Set_URDocument", params))
        pismo.otvet = otvet[:2000]
    except Exception as e:   # ошибка одного документа не прерывает рассылку
        pismo.oshibka = f"{type(e).__name__}: {e}"[:2000] if not isinstance(e, kredo.KredoError) else str(e)[:2000]
        pismo.save()
        return pismo
    pismo.status = Pismo.OK
    pismo.kredo_doc = doc_id(otvet)
    pismo.save()
    return pismo


def doc_id(otvet):
    """Код документа в КРЭДО из ответа Set_URDocument (<ret_val>GUID</ret_val>)."""
    m = re.search(r"<ret_val>\s*([0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27})\s*</ret_val>", otvet or "")
    return m.group(1).upper() if m else ""


def obnovit_statusy(cod_gor, invoker=None):
    """Статусы отправленных участком документов (Kredo_DocumentsOut, кнопка
    «Данные об исходящих электронных документах» старой программы) — в реестр
    писем. Ответ сохраняется в dokumenty\\kredo\\documentsout_<участок>.xml.
    Возвращает (обновлено писем, документов в ответе КРЭДО)."""
    from django.utils import timezone
    from .kredo_kody import tablica
    _, pid_out = otpravitel(cod_gor)
    comorg = kredo.nastrojki(cod_gor)["comorg"]
    otvet = kredo.proverit((invoker or kredo.ComInvoker(cod_gor)).exec_proc(
        "Kredo_DocumentsOut", f"@comorg={comorg},@pid_out={pid_out}"))
    with contextlib.suppress(OSError):
        papka = pdf.base_dir() / "kredo"
        papka.mkdir(parents=True, exist_ok=True)
        (papka / f"documentsout_{cod_gor}.xml").write_text(otvet, encoding="utf-8")
    rows = {r["doc_id"].strip().upper(): r for r in tablica(otvet, "doc_id") if r.get("doc_id")}
    obnovleno, sejchas = 0, timezone.now()
    for z in Pismo.objects.filter(kanal=Pismo.KREDO, status=Pismo.OK, cod_gor=cod_gor).exclude(kredo_doc=""):
        r = rows.get(z.kredo_doc.upper())
        if r is None:
            continue
        z.kredo_out, z.kredo_in = (r.get("dstn_out") or "")[:200], (r.get("dstn_in") or "")[:200]
        z.kredo_data = sejchas
        z.save(update_fields=["kredo_out", "kredo_in", "kredo_data"])
        obnovleno += 1
    return obnovleno, len(rows)


def ne_prochitan(z):
    """Документ ещё не получен абонентом: статус у получателя «ожидает…»."""
    return "ожида" in (z.kredo_in or "").lower()


def otozvat(z, user="", invoker=None):
    """Отозвать (удалить) из КРЭДО отправленный документ, пока абонент его не
    получил: процедура Set_URDocumentDelete (кнопка «Удалить документ» формы
    doc_kredo старой программы). Перед удалением статус запрашивается заново.
    Возвращает запись реестра; при отказе — KredoError."""
    from django.utils import timezone
    if z.kanal != Pismo.KREDO or z.status != Pismo.OK or not z.kredo_doc:
        raise kredo.KredoError("Отозвать можно только документ, отправленный в КРЭДО")
    inv = invoker or kredo.ComInvoker(z.cod_gor)
    obnovit_statusy(z.cod_gor, invoker=inv)
    z.refresh_from_db()
    if not ne_prochitan(z):
        raise kredo.KredoError(f"Документ № {z.nomer} не отозван: статус у абонента «{z.kredo_in or 'неизвестен'}», "
                               f"отозвать можно только неполученный")
    otvet = kredo.proverit(inv.exec_proc("Set_URDocumentDelete", f"@doc_id={z.kredo_doc}"))
    z.status, z.otozvano, z.otozval = Pismo.OTOZVANO, timezone.now(), user[:150]
    z.otvet = (z.otvet + "\n--- отзыв ---\n" + otvet)[:4000]
    z.save(update_fields=["status", "otozvano", "otozval", "otvet"])
    return z


def rassylka(cod_gor, nomera, context, user="", mesyac=None, proverka=False):
    from . import documents
    out = []
    for nom in nomera:
        dok = documents.sobrat(cod_gor, nom, mesyac=mesyac)
        if dok is not None:
            out.append(otpravit(dok, context, user, proverka=proverka))
    return out
