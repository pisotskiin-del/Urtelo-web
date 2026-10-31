"""Карта абонента (форма karta старой программы), поиск абонентов и карта
договора (форма karta_dog). Абонент — запись таблицы potreb, в адресах
используется его лицевой № (potreb_id)."""

import datetime
import re
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError, Q, Sum, Value
from django.db.models.functions import Replace
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import formats, timezone

from django.db import transaction

from catalogs.models import Akcept, Bank, Danrasch, GvsKot, Kategorpot, Limit, Potreb, SpTeplosch, SpTeplpoteri
from teplo.sqlite_unicode import UnicodeLower

from . import documents, layout, nov_mes, poteri, raschet, reports
from .forms import DanRaschForm, NovAbonentForm, PoteriForm, TeploschForm, karta_form

view_required = permission_required("catalogs.view_potreb", raise_exception=True)


def _cities():
    return list(Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod"))


def _current_city(request, cities):
    codes = [c.cod_gorod for c in cities]
    raw = request.GET.get("gorod")
    if raw and raw.isdigit() and int(raw) in codes:
        request.session["kod_gorod"] = int(raw)
    code = request.session.get("kod_gorod")
    if code not in codes:
        code = codes[0] if codes else None
    return code


def _papka_1c():
    from .models import Nastroika
    return Nastroika.papka()


def _int(value):
    value = (value or "").strip()
    return int(value) if value.isdigit() else None


@login_required
@view_required
def index(request):
    """Поиск абонента: по № договора, по наименованию и по лицевому №, как
    в нижней части старой карты. Поиск по № договора и наименованию — в
    выбранном городе, по лицевому № — во всех."""
    cities = _cities()
    city = _current_city(request, cities)
    dog, ls, sub = _int(request.GET.get("dog")), _int(request.GET.get("ls")), _int(request.GET.get("sub"))
    name = request.GET.get("q", "").strip()

    if request.GET.get("ls") is not None:
        found = Potreb.objects.filter(potreb_id=ls).first() if ls is not None else None
        if found:
            return redirect("abonents:karta", potreb_id=found.potreb_id)
        messages.warning(request, "Абонент с таким лицевым № не найден")

    # Галочка «Только активные лицевые счета» запоминается до выхода.
    if "aktiv" in request.GET:
        request.session["aktiv"] = request.GET.get("aktiv") == "1"
    aktiv = request.session.get("aktiv", True)
    qs = Potreb.objects.filter(cod_gor=city).select_related("cod_gor").order_by("pk")
    if aktiv:
        qs = qs.filter(d_stat__in=layout.RASCHET)
    if dog is not None:
        qs = qs.filter(nom_dog=dog)
    if sub is not None:
        qs = qs.filter(nom_dogab=sub)
    if name:
        # Старая программа ищет без учёта регистра и пробелов.
        needle = name.replace(" ", "").lower()
        qs = qs.alias(_name=Replace(UnicodeLower("name_potre"), Value(" "), Value(""))).filter(_name__contains=needle)
    if dog is not None and not name and sub is None and qs.count() == 1:
        return redirect("abonents:karta", potreb_id=qs.get().potreb_id)

    page = Paginator(qs, settings.CATALOG_PAGE_SIZE).get_page(request.GET.get("page"))
    kategor = dict(Kategorpot.objects.values_list("id_kotegor", "name_kateg"))
    rows = [(p, kategor.get(p.id_kategor, ""), _address(p)) for p in page]
    params = request.GET.copy()
    params.pop("page", None)
    params.pop("ls", None)
    return render(request, "abonents/index.html", {
        "cities": cities, "city": city, "rows": rows, "page": page,
        "dog": request.GET.get("dog", ""), "q": name, "sub": sub,
        "query": params.urlencode(), "aktiv": aktiv, "filtered": dog is not None or sub is not None or bool(name),
    })


def _address(p):
    parts = [(p.adres_sd or "").strip()]
    if (p.oba_dom or "").strip():
        parts.append("дом " + p.oba_dom.strip())
    if (p.oba_kv or "").strip():
        parts.append("кв. " + p.oba_kv.strip())
    return " ".join(x for x in parts if x)


def related_values(p):
    """Значения из справочников, которые старая карта показывала через связи
    своего окружения данных (danrasch, minist, kategorpot, gvs_kot, bank)."""
    city = p.cod_gor
    kategor = Kategorpot.objects.filter(id_kotegor=p.id_kategor).first() if p.id_kategor else None
    kotel = GvsKot.objects.filter(id_kot=p.id_koteln).first() if p.id_koteln else None
    bank = Bank.objects.filter(cod_banka=p.cod_banka).first() if p.cod_banka else None
    month = " ".join(str(x).strip() for x in (city.name_mes, city.god) if x) if city else ""
    return {
        "@gorod": city.name_gorod if city else None,
        "@mes": month,
        "@minist": p.cod_minist.name_minis if p.cod_minist_id else None,
        "@kategor": kategor.name_kateg if kategor else None,
        "@kotel": kotel.name_kot if kotel else None,
        "@bank": bank.name_banka if bank else None,
        "@t_vozd": city.t_vozd if city else None,
        "@tkoef": city.tkoef if city else None,
    }


def _display(f, value, extra):
    if value is None or value == "" or (f.link and value == 0):
        return None
    if f.name in layout.CHOICES:
        return dict(layout.CHOICES[f.name]).get(value, value)
    if f.name in extra:
        return extra[f.name].get(value, value)
    if isinstance(value, datetime.datetime):
        return formats.date_format(timezone.localtime(value), "d.m.Y H:i")
    if isinstance(value, datetime.date):
        return formats.date_format(value, "d.m.Y")
    if isinstance(value, bool):
        return "да" if value else "нет"
    if isinstance(value, Decimal):
        return formats.localize(value)
    return str(value).strip() or None


def _items(p, fields, related, form=None, lookups=None):
    items = []
    for f in fields:
        value = related[f.name] if f.related else getattr(p, f.name)
        if f.name == "cod_minist":
            value = p.cod_minist.name_minis if p.cod_minist_id else None
        item = {"f": f, "value": _display(f, value, lookups or {}), "url": None, "field": None}
        if form is not None and not f.ro and f.name in form.fields:
            item["field"] = form[f.name]
        if f.link and value:
            item["url"] = reverse("abonents:karta", args=[value])
        items.append(item)
    return items


def _lookups():
    return {
        "accept": dict(Akcept.objects.values_list("id_akc", "name_akc")),
        "id_kategor": dict(Kategorpot.objects.values_list("id_kotegor", "name_kateg")),
        "id_koteln": dict(GvsKot.objects.values_list("id_kot", "name_kot")),
    }


def _neighbours(p):
    same_city = Potreb.objects.filter(cod_gor=p.cod_gor_id).exclude(potreb_id=None)
    first = same_city.order_by("pk").values_list("potreb_id", flat=True).first()
    last = same_city.order_by("-pk").values_list("potreb_id", flat=True).first()
    prev = same_city.filter(pk__lt=p.pk).order_by("-pk").values_list("potreb_id", flat=True).first()
    nxt = same_city.filter(pk__gt=p.pk).order_by("pk").values_list("potreb_id", flat=True).first()
    position = same_city.filter(pk__lte=p.pk).count()
    return {"first": first, "prev": prev, "next": nxt, "last": last,
            "position": position, "total": same_city.count()}


def _prisoed(p):
    """Присоединённые объекты абонента: [(вид, поле, лицевой №, абонент или None)]."""
    found = []
    for kind, (label, names) in layout.PRISOED.items():
        for name in names:
            value = getattr(p, name)
            if value:
                found.append((label, name, value))
    objects = {o.potreb_id: o for o in Potreb.objects.filter(potreb_id__in=[v for _, _, v in found])}
    return [(label, name, value, objects.get(value)) for label, name, value in found]


def _hero(p, related):
    """Сводка для шапки карты: (иконка, подпись, значение) в две колонки."""
    def s(*parts):
        text = " ".join(str(x).strip() for x in parts if x not in (None, "", 0) and str(x).strip())
        return text or None
    date = formats.date_format(p.data_dog, "d.m.Y") if p.data_dog else None
    left = [
        ("pin", "Населённый пункт", related["@gorod"]),
        ("building", "Адрес объекта", s(p.adres_sd, p.oba_dom and f"дом {str(p.oba_dom).strip()}", p.oba_kv and f"кв. {str(p.oba_kv).strip()}")),
        ("flame", "Подключен к", related["@kotel"]),
        ("book", "Министерство", related["@minist"]),
        ("calendar", "Расчетный месяц", related["@mes"]),
    ]
    right = [
        ("phone", "Телефон", s(p.telefon)),
        ("open", "E-mail", s(p.mail)),
        ("user", "Руководитель", s(p.direktor)),
        ("calendar", "Дата договора", date),
        ("sliders", "Способ расчёта", dict(layout.TIP_RASOT).get(p.tip_rasot)),
    ]
    return {"kategor": related["@kategor"], "left": left, "right": right}


SPOSOB = ("tip_rasot", "tip_rasgvs")  # переключатели «Способ расчёта» на вкладках


def _sposob(p, groups):
    """Переключатель способа расчёта на карте: (поле, текущее значение, варианты) или None."""
    for _, fields in groups:
        for f in fields:
            if f.name in SPOSOB:
                return f.name, getattr(p, f.name), layout.CHOICES[f.name]
    return None


def _card_context(request, p, tab_key, form=None):
    related = related_values(p)
    lookups = _lookups()
    _, title, groups = layout.tab(tab_key)
    return {
        "p": p,
        "otkluchen": p.d_stat in layout.OTKLUCHEN,
        "header": _items(p, layout.HEADER, related, form, lookups),
        "groups": [(g, _items(p, fields, related, form, lookups)) for g, fields in groups],
        "tabs": [(k, t) for k, t, _ in layout.TABS], "tab": tab_key, "tab_title": title,
        "tab_url": reverse("abonents:edit" if form is not None else "abonents:karta", args=[p.potreb_id]),
        "nav": _neighbours(p),
        "prisoed": _prisoed(p) if tab_key == "otop" else [],
        "prisoed_kinds": [(k, label) for k, (label, _) in layout.PRISOED.items()],
        "sposob": _sposob(p, groups),
        "rasot_label": dict(layout.TIP_RASOT).get(p.tip_rasot, ""),
        "hero": _hero(p, related),
        "can_change": request.user.has_perm("catalogs.change_potreb"),
        "can_delete": request.user.has_perm("catalogs.delete_potreb"),
    }


def _tab_key(request):
    key = request.GET.get("tab") or request.POST.get("tab")
    return key if key in layout.TAB_KEYS else layout.TAB_KEYS[0]


@login_required
@view_required
def karta(request, potreb_id):
    p = get_object_or_404(Potreb.objects.select_related("cod_gor", "cod_minist"), potreb_id=potreb_id)
    if p.cod_gor_id:
        request.session["kod_gorod"] = p.cod_gor_id
    return render(request, "abonents/karta.html", _card_context(request, p, _tab_key(request)))


@login_required
@permission_required("catalogs.change_potreb", raise_exception=True)
def karta_edit(request, potreb_id):
    p = get_object_or_404(Potreb.objects.select_related("cod_gor", "cod_minist"), potreb_id=potreb_id)
    tab_key = _tab_key(request)
    form = karta_form(tab_key, request.POST or None, instance=p)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Изменения сохранены")
        return redirect(reverse("abonents:karta", args=[p.potreb_id]) + f"?tab={tab_key}")
    context = _card_context(request, p, tab_key, form)
    context["form"] = form
    return render(request, "abonents/karta_edit.html", context)


@login_required
@permission_required("catalogs.delete_potreb", raise_exception=True)
def karta_delete(request, potreb_id):
    p = get_object_or_404(Potreb, potreb_id=potreb_id)
    if request.method == "POST":
        try:
            p.delete()
        except ProtectedError as exc:
            tables = sorted({o._meta.db_table for o in exc.protected_objects})
            messages.error(request, "Запись нельзя удалить: на неё ссылаются таблицы " + ", ".join(tables))
            return redirect("abonents:karta", potreb_id=potreb_id)
        messages.success(request, "Запись удалена")
        return redirect("abonents:index")
    return render(request, "abonents/confirm_delete.html", {"p": p})


@login_required
@view_required
def dogovor(request, cod_gor, nom_dog):
    """Карта договора: все объекты договора в городе с итогами начислений."""
    city = get_object_or_404(Danrasch, cod_gorod=cod_gor)
    qs = Potreb.objects.filter(cod_gor=city, nom_dog=nom_dog).order_by("potreb_id")
    columns = ["nac_vsego", "nach_otpr", "nach_otnag", "nach_gvs", "poter_pr", "poter_nag"]
    totals = qs.aggregate(**{c: Sum(c) for c in columns})
    katabon = dict(layout.ID_KATABON)
    rows = [(p, [getattr(p, c) for c in columns], katabon.get(p.id_katabon, ""), _address(p)) for p in qs]
    return render(request, "abonents/dogovor.html", {
        "city": city, "nom_dog": nom_dog, "rows": rows,
        "totals": [totals[c] for c in columns], "current": _int(request.GET.get("ls")),
    })


@login_required
@permission_required("catalogs.add_potreb", raise_exception=True)
def nov_abonent(request):
    """Ввод нового абонента: лицевой № присваивается следующий по порядку."""
    city = _current_city(request, _cities())
    form = NovAbonentForm(request.POST or None, city=city)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            p = form.save()
        messages.success(request, f"Абонент добавлен, лицевой № {p.potreb_id}")
        return redirect(reverse("abonents:edit", args=[p.potreb_id]) + "?tab=ishod")
    return render(request, "abonents/nov_abonent.html", {"form": form})


def _sub_record(model, p, **defaults):
    """Запись дополнительной таблицы абонента (связь по ln = potreb_id).
    Как в старой программе, создаётся при первом сохранении."""
    obj = model.objects.filter(ln=p.potreb_id).order_by("pk").first()
    return obj or model(ln=p.potreb_id, **defaults)


@login_required
@permission_required("catalogs.view_spteplpoteri", raise_exception=True)
def poteri_view(request, potreb_id):
    p = get_object_or_404(Potreb, potreb_id=potreb_id)
    sp = _sub_record(SpTeplpoteri, p)
    can_change = request.user.has_perm("catalogs.change_spteplpoteri") and request.user.has_perm(
        "catalogs.change_potreb")
    form = PoteriForm(request.POST or None, instance=sp)
    if request.method == "POST":
        if not can_change:
            raise PermissionDenied
        if form.is_valid():
            with transaction.atomic():
                sp = form.save(commit=False)
                if "raschet" in request.POST:
                    total = poteri.raschet(sp, p)
                    p.save(update_fields=["poter_pr", "poter_nag"])
                    messages.success(request, f"Потери рассчитаны: всего {formats.localize(total)} Гкал")
                else:
                    messages.success(request, "Изменения сохранены")
                sp.save()
            return redirect("abonents:poteri", potreb_id=p.potreb_id)
    rows = [(i, form[f"diametr{i}"], form[f"dlina{i}"], getattr(sp, f"poteri_pr{i}")) for i in poteri.SECTIONS]
    return render(request, "abonents/poteri.html", {
        "p": p, "sp": sp, "form": form, "rows": rows, "can_change": can_change,
    })


@login_required
@permission_required("catalogs.view_spteplosch", raise_exception=True)
def teplosch_view(request, potreb_id):
    p = get_object_or_404(Potreb, potreb_id=potreb_id)
    obj = _sub_record(SpTeplosch, p, name_obek=p.name_potre or "", adres_obek=p.adres_sd or "")
    can_change = request.user.has_perm("catalogs.change_spteplosch")
    form = TeploschForm(request.POST or None, instance=obj)
    if request.method == "POST":
        if not can_change:
            raise PermissionDenied
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect(reverse("abonents:karta", args=[p.potreb_id]) + "?tab=ishod")
    return render(request, "abonents/teplosch.html", {"p": p, "form": form, "can_change": can_change})


@login_required
@permission_required("catalogs.view_danrasch", raise_exception=True)
def dan_rasch(request):
    """Исходные данные для расчета по городу (форма dan_rasch): температура,
    t коэффициент, дни отопления и ГВС, фактический отпуск Q."""
    cities = _cities()
    city = _current_city(request, cities)
    d = get_object_or_404(Danrasch, cod_gorod=city)
    can_change = request.user.has_perm("catalogs.change_danrasch") and request.user.has_perm(
        "catalogs.change_potreb")
    form = DanRaschForm(request.POST or None, instance=d)
    if request.method == "POST":
        if not can_change:
            raise PermissionDenied
        if form.is_valid():
            with transaction.atomic():
                d = form.save()
                in_city = Potreb.objects.filter(cod_gor=city)
                changes = {}
                if form.cleaned_data["dnotop_vsem"]:
                    changes["dnotop"] = d.dnotop or 0
                if form.cleaned_data["dngvs_vsem"]:
                    changes["dngvs"] = d.dngvs or 0
                if changes:
                    # У отключённых абонентов (договор расторгнут или приостановлен) 0 дней.
                    in_city.exclude(d_stat__in=layout.OTKLUCHEN).update(**changes)
                    in_city.filter(d_stat__in=layout.OTKLUCHEN).update(**{name: 0 for name in changes})
                # Как кнопка «Выход» старой формы: название котельной в записях абонентов.
                for kot in GvsKot.objects.filter(kod_gor=city):
                    in_city.filter(id_koteln=kot.id_kot).exclude(name_kot=kot.name_kot).update(name_kot=kot.name_kot)
            messages.success(request, f"Сохранено. t коэффициент: {formats.localize(d.tkoef)}"
                             + (f"; дни записаны {in_city.exclude(d_stat__in=layout.OTKLUCHEN).count()} абонентам, "
                                f"у отключённых 0" if changes else ""))
            return redirect("abonents:dan_rasch")
    return render(request, "abonents/dan_rasch.html", {
        "cities": cities, "city": city, "d": d, "form": form, "can_change": can_change,
    })


ITOG_FIELDS = [
    ("nach_otpr", "Начислено по прибору"), ("nach_otnag", "Начислено по расчету"),
    ("nac_pogaz", "Начислено по факту"), ("poter_pr", "Потери по прибору"), ("poter_nag", "Потери по нагрузке"),
    ("gkl_perer", "Перерасчет"), ("nach_otopl", "Отопление, факт. потребление"), ("nach_gvs", "ГВС"),
    ("poter_gvs", "Тепловые потери ГВС"), ("nac_vsego", "Предъявлено к оплате"),
]


@login_required
@permission_required("catalogs.view_potreb", raise_exception=True)
def raschet_view(request):
    """Расчет начислений по всем абонентам (кнопка «Расчет» карты)."""
    can_run = request.user.has_perm("catalogs.change_potreb")
    if request.method == "POST":
        if not can_run:
            raise PermissionDenied
        result = raschet.run()
        request.session["raschet_itog"] = {
            "time": formats.localize(timezone.localtime()),
            "potreb": result.potreb,
            "created_poteri": result.created_poteri,
            "zero_division": result.zero_division,
            "otkluchen": result.otkluchen,
        }
        messages.success(request, f"Расчет закончен: рассчитано абонентов {result.potreb}")
        return redirect("abonents:raschet_itog")
    cities = _cities()
    counts = {row["cod_gor"]: row for row in Potreb.objects.values("cod_gor").annotate(
        n=Count("pk"), dn=Count("pk", filter=Q(dnotop__gt=0)))}
    rows = [(c, counts.get(c.cod_gorod, {}).get("n", 0), counts.get(c.cod_gorod, {}).get("dn", 0)) for c in cities]
    return render(request, "abonents/raschet.html", {"rows": rows, "can_run": can_run})


@login_required
@permission_required("catalogs.view_potreb", raise_exception=True)
def raschet_itog(request):
    """Итоги расчета по городам (только рассчитанные лицевые счета, каждое
    число открывает расшифровку по абонентам) и абоненты, у которых
    заканчивается лимит (таблица limit, её заполняет расчет)."""
    cities = _cities()
    qs = Potreb.objects.filter(d_stat__in=layout.RASCHET)
    sums = {row["cod_gor"]: row for row in qs.values("cod_gor").annotate(
        **{name: Sum(name) for name, _ in ITOG_FIELDS})}
    url = reverse("abonents:raschet_rasshifr")
    table = [(label, [(sums.get(c.cod_gorod, {}).get(name) or 0, f"{url}?gorod={c.cod_gorod}&pole={name}")
                      for c in cities]) for name, label in ITOG_FIELDS]
    # Суммы у лицевых счетов, которые расчет не трогает (договор не заключён):
    # остались от прежних расчетов и в итоги не входят.
    stale = Potreb.objects.exclude(d_stat__in=layout.RASCHET).exclude(nac_vsego=0).exclude(nac_vsego=None)
    return render(request, "abonents/raschet_itog.html", {
        "cities": cities, "table": table, "info": request.session.get("raschet_itog"),
        "limits": Limit.objects.order_by("potreb_id"), "stale": stale.order_by("cod_gor", "potreb_id"),
    })


@login_required
@view_required
def raschet_rasshifr(request):
    """Расшифровка числа из итогов расчета: абоненты города, у которых это
    поле не 0."""
    labels = dict(ITOG_FIELDS)
    pole = request.GET.get("pole")
    city = Danrasch.objects.filter(cod_gorod=_int(request.GET.get("gorod"))).first()
    if pole not in labels or city is None:
        raise Http404
    qs = (Potreb.objects.filter(cod_gor=city.cod_gorod, d_stat__in=layout.RASCHET)
          .exclude(**{pole: 0}).exclude(**{pole: None}).order_by("potreb_id"))
    cols = [reports.Col("Л/№", "int"), reports.Col("№ дог."), reports.Col("Наименование"), reports.Col("Объект"),
            reports.Col("Принадлежность"), reports.Col("Способ расчета")]
    extra = [("nach_otopl", "Отопление"), ("nach_gvs", "ГВС"), ("poter_gvs", "Потери ГВС")] if pole == "nac_vsego" else []
    cols += [reports.Col(t, "num", 3, total=True) for _, t in extra]
    if pole == "nac_vsego":
        cols.append(reports.Col("С объектов договора", "num", 3, total=True))
    cols.append(reports.Col(labels[pole], "num", 3, total=True))
    katabon, sposob = dict(layout.ID_KATABON), dict(layout.TIP_RASOT)
    rows = []
    for p in qs:
        row = [p.potreb_id, p.nom_dog, p.name_potre, p.glav_potre, katabon.get(p.id_katabon, p.id_katabon),
               sposob.get(p.tip_rasot, p.tip_rasot)]
        row += [getattr(p, f) or 0 for f, _ in extra]
        if pole == "nac_vsego":
            row.append((p.nac_vsego or 0) - sum((getattr(p, f) or 0 for f, _ in extra), Decimal(0)))
        row.append(getattr(p, pole))
        rows.append(row)
    sec = reports.Section(rows=rows)
    sec.links = [[reverse("abonents:karta", args=[r[0]])] + [None] * (len(r) - 1) for r in rows]
    report = reports.Report(f"Итоги расчета: {labels[pole]}", [f"г. {(city.name_gorod or '').strip()}",
                            f"за {(city.name_mes or '').strip()} {city.god} г."],
                            [reports.Table(cols, [sec], total=reports._sum_row(cols, rows, "Итого", label_col=2))],
                            notes=[f"Абонентов: {len(rows)}"], landscape=True)
    return render(request, "abonents/raschet_rasshifr.html", {"report": report})


@login_required
@permission_required("catalogs.change_potreb", raise_exception=True)
def prisoed(request, potreb_id):
    """Добавить присоединённый объект в первое свободное поле или убрать его."""
    p = get_object_or_404(Potreb, potreb_id=potreb_id)
    back = redirect(reverse("abonents:karta", args=[p.potreb_id]) + "?tab=otop")
    if request.method != "POST":
        return back
    slots = {name: kind for kind, (_, names) in layout.PRISOED.items() for name in names}
    remove = request.POST.get("remove")
    if remove:
        if remove in slots and getattr(p, remove):
            old = getattr(p, remove)
            setattr(p, remove, 0)
            p.save(update_fields=[remove])
            messages.success(request, f"Объект л/№ {old} убран из присоединённых")
        return back
    kind = request.POST.get("kind")
    ls = _int(request.POST.get("ls"))
    if kind not in layout.PRISOED:
        messages.error(request, "Выберите, что присоединяется: прибор или нагрузка")
        return back
    label, names = layout.PRISOED[kind]
    obj = Potreb.objects.filter(potreb_id=ls).first() if ls else None
    if obj is None:
        messages.error(request, f"Абонент с лицевым № {request.POST.get('ls', '').strip()} не найден")
    elif obj.potreb_id == p.potreb_id:
        messages.error(request, "Нельзя присоединить абонента к самому себе")
    elif obj.d_stat in layout.OTKLUCHEN:
        status = (obj.d_stat_val or dict(layout.D_STAT).get(obj.d_stat, "")).strip().lower()
        messages.error(request, f"Л/№ {obj.potreb_id} {status}: присоединить можно только действующий лицевой счет")
    elif any(getattr(p, name) == obj.potreb_id for name in names):
        messages.warning(request, f"Л/№ {obj.potreb_id} уже присоединён")
    else:
        free = next((name for name in names if not getattr(p, name)), None)
        if free is None:
            messages.error(request, f"Свободных мест нет: можно присоединить не больше {len(names)}")
        else:
            setattr(p, free, obj.potreb_id)
            p.save(update_fields=[free])
            messages.success(request, f"{label}: л/№ {obj.potreb_id} {obj.name_potre or ''}".strip())
    return back


@login_required
@permission_required("catalogs.change_potreb", raise_exception=True)
def sposob(request, potreb_id):
    """Сменить способ расчёта прямо с карты (кнопки «по прибору» / «по нагрузке»)."""
    p = get_object_or_404(Potreb, potreb_id=potreb_id)
    name = request.POST.get("field")
    tab = "gvs" if name == "tip_rasgvs" else "otop"
    if request.method == "POST" and name in SPOSOB:
        choices = dict(layout.CHOICES[name])
        value = _int(request.POST.get("value"))
        if value in choices and value != getattr(p, name):
            setattr(p, name, value)
            p.save(update_fields=[name])
            messages.success(request, f"Способ расчёта: {choices[value]}. Начисления пересчитаются при следующем расчёте.")
    return redirect(reverse("abonents:karta", args=[p.potreb_id]) + f"?tab={tab}")


@login_required
@permission_required("catalogs.view_potreb", raise_exception=True)
def nov_mes_view(request):
    """Переход на новый месяц (форма nov_mes): архив месяца, накопления с начала
    года и сезона, обнуление начислений, следующий месяц во всех городах.
    Выполняет только Администратор; последний переход можно отменить."""
    can_run = request.user.has_perm("catalogs.delete_danrasch")
    if request.method == "POST":
        if not can_run:
            raise PermissionDenied
        if request.POST.get("action") == "undo":
            try:
                arh = nov_mes.undo()
            except ValueError as e:
                messages.error(request, str(e))
            else:
                messages.success(request, f"Переход отменён: снова {nov_mes.MONTHS[arh.nom_mes - 1]} {arh.god}")
        elif request.POST.get("ready") != "1":
            messages.error(request, "Отметьте, что расчет выполнен и итоги сверены")
        else:
            r = nov_mes.run(request.user.get_full_name() or request.user.username)
            messages.success(request, f"Выполнен переход к новому месяцу: {nov_mes.MONTHS[r.opened[0] - 1]} {r.opened[1]}. "
                                      f"Месяц {nov_mes.MONTHS[r.closed[0] - 1]} {r.closed[1]} сохранён в архиве.")
            try:
                path = nov_mes.export_1c(nov_mes.last())
            except OSError as e:
                messages.error(request, f"Файл для 1С не записан в папку: {e}. Скачайте его в «Закрытых месяцах».")
            else:
                if path:
                    messages.success(request, f"Файл для 1С: {path} (записей {r.abot})")
        return redirect("abonents:nov_mes")
    mes, god = nov_mes.current()
    nxt = nov_mes.next_month(mes, god) if mes else None
    cities = _cities()
    sums = {row["cod_gor"]: row for row in Potreb.objects.values("cod_gor").annotate(
        n=Count("pk"), s=Sum("nac_vsego"), nach=Count("pk", filter=Q(nac_vsego__gt=0)))}
    rows = [(c, sums.get(c.cod_gorod, {})) for c in cities]
    return render(request, "abonents/nov_mes.html", {
        "mes": mes and nov_mes.MONTHS[mes - 1], "god": god, "next": nxt and f"{nov_mes.MONTHS[nxt[0] - 1]} {nxt[1]}",
        "rows": rows, "can_run": can_run, "arhiv": nov_mes.MesArhiv.objects.filter(istochnik=nov_mes.MesArhiv.WEB).defer("data")[:24],
        "last": nov_mes.last(), "dir_1c": _papka_1c(), "year_reset": nxt and nxt[0] == 1, "season_reset": nxt and nxt[0] == 10,
    })


@login_required
@permission_required("catalogs.view_potreb", raise_exception=True)
def abot_1c(request, pk):
    """Скачать выгрузку в 1С закрытого месяца: Abpt<ГГ><ММ>.dbf, как в старой программе."""
    arh = get_object_or_404(nov_mes.MesArhiv, pk=pk)
    response = HttpResponse(content_type="application/x-dbf")
    response["Content-Disposition"] = f'attachment; filename="{nov_mes.abot_filename(arh.nom_mes, arh.god)}"'
    nov_mes.write_abot(arh, response)
    return response


@login_required
@view_required
def otchety(request):
    """Список отчетов: форма «Отчеты» и меню «Печать» старой программы."""
    groups = {}
    for r in reports.REPORTS:
        groups.setdefault(r.group, []).append(r)
    return render(request, "abonents/otchety.html", {"groups": groups.items()})


@login_required
@view_required
def polez_rasshifr(request):
    """Расшифровка ячейки «Полезного отпуска»: список абонентов, из которых
    она сложилась (ссылки на карты), на экране и в Excel."""
    report = reports.polez_rasshifr(request.GET)
    if report is None:
        raise Http404
    if request.GET.get("xlsx"):
        import io
        buf = io.BytesIO()
        reports.to_xlsx(report, buf)
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="polez_rasshifr.xlsx"'
        return response
    table = report.tables[0]
    table.sections[0].links = [[None, reverse("abonents:karta", args=[r[1]])] + [None] * (len(r) - 2)
                               for r in table.sections[0].rows]
    query = request.GET.copy()
    query["xlsx"] = "1"
    back = reverse("abonents:otchet", args=["polez_otpusk"]) + (f"?vid={request.GET['vid']}" if request.GET.get("vid") else "")
    return render(request, "abonents/rasshifr.html", {"report": report, "xlsx_query": query.urlencode(), "back": back})


@login_required
@view_required
def otchet(request, key):
    """Отчет на экране, для печати и в Excel (?xlsx=1)."""
    rdef = reports.BY_KEY.get(key)
    if rdef is None:
        raise Http404
    cities = _cities()
    code = _current_city(request, cities)
    city = next((c for c in cities if c.cod_gorod == code), None)
    if city is None:
        raise Http404
    report, opts = reports.build(rdef, city, request.GET)
    if request.GET.get("xlsx"):
        import io
        buf = io.BytesIO()
        reports.to_xlsx(report, buf)
        name = f"{rdef.key}_{city.cod_gorod}.xlsx" if rdef.per_city else f"{rdef.key}.xlsx"
        response = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{name}"'
        return response
    query = request.GET.copy()
    query["xlsx"] = "1"
    return render(request, "abonents/otchet.html", {
        "rdef": rdef, "report": report, "opts": opts, "options": reports.options_for(rdef),
        "cities": cities, "city": code, "xlsx_query": query.urlencode(),
    })


DOKUMENTY = {"schet": "Информация-счёт", "akt": "Акт о фактическом потреблении"}


def _dok_context(dok):
    """Подписи и реквизиты для шаблона документа."""
    from .models import Podpisant
    from catalogs.models import SmtpNas
    ved = Podpisant.get(Podpisant.VED_SPEC, dok.gorod)
    isp = Podpisant.get(Podpisant.ISPOLNITEL, dok.gorod)
    akt = Podpisant.get(Podpisant.AKT, dok.gorod)
    smtp = SmtpNas.objects.first()
    return {"dok": dok, "org": documents.ORG, "ved": ved, "isp": isp,
            "akt_lico": " ".join(x for x in akt if x) or
            "ведущего специалиста Рыбницкого участка по эксплуатации котельных и тепловых сетей "
            "Борсуковского Сергея Васильевича",
            "dov": (smtp.nom_dov, smtp.data_dov) if smtp and smtp.nom_dov else None}


@login_required
@view_required
def dokument(request, cod_gor, nom_dog, vid):
    """«Информация-счёт» (vid=schet) или акт (vid=akt) по договору за текущий
    месяц участка: на экране и для печати (в PDF — печатью из браузера)."""
    if vid not in DOKUMENTY:
        raise Http404
    dok = documents.sobrat(cod_gor, nom_dog)
    if dok is None:
        raise Http404("В договоре нет действующих лицевых счетов")
    if request.GET.get("pdf"):
        from . import pdf
        path = pdf.save(dok, vid, _dok_context(dok))
        response = HttpResponse(path.read_bytes(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{path.name}"'
        return response
    if request.method == "POST" and request.POST.get("action") == "send":
        if not request.user.has_perm("catalogs.change_potreb"):
            raise PermissionDenied
        from . import pochta
        problem = pochta.gotovo()
        if problem:
            messages.error(request, problem)
        else:
            z = pochta.otpravit(dok, vid, _dok_context(dok), request.user.get_username())
            if z.status == z.OK:
                messages.success(request, f"Документ № {z.nomer} отправлен на {z.email}")
            else:
                messages.error(request, f"Не отправлено: {z.oshibka}")
        return redirect(request.get_full_path())
    from . import pochta
    poluch = pochta.poluchatel(dok)
    return render(request, "abonents/dokument.html", {
        **_dok_context(dok), "vid": vid, "title": DOKUMENTY[vid], "doks": [dok],
        "email": poluch.mail.strip() if poluch else "", "can_send": request.user.has_perm("catalogs.change_potreb"),
        "back": reverse("abonents:karta", args=[int(request.GET["ls"])]) if request.GET.get("ls", "").isdigit()
        else reverse("abonents:dogovor", args=[cod_gor, nom_dog]),
    })


@login_required
@view_required
def dokumenty(request):
    """Пакет документов участка за месяц: по каждому договору с начислением
    больше нуля, каждый документ с новой страницы."""
    vid = request.GET.get("vid", "schet")
    if vid not in DOKUMENTY:
        raise Http404
    cities = _cities()
    code = _current_city(request, cities)
    doks = [d for d in (documents.sobrat(code, n) for n in documents.dogovory(code)) if d]
    ctx = _dok_context(doks[0]) if doks else {"org": documents.ORG}
    if request.GET.get("pdf") and doks:
        from . import pdf
        for d in doks:   # каждый документ — в папку месяца, как в старой программе
            pdf.save(d, vid, ctx)
        response = HttpResponse(pdf.render(doks, vid, ctx), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{vid}_{code}_{doks[0].god}_{doks[0].mes:02d}.pdf"'
        return response
    return render(request, "abonents/dokument.html", {
        **ctx, "vid": vid, "title": DOKUMENTY[vid], "doks": doks, "paket": True,
        "cities": cities, "city": code, "vidy": DOKUMENTY.items(),
        "back": reverse("abonents:otchety"),
    })


@login_required
@view_required
def rassylka(request):
    """Рассылка документов по почте за текущий месяц участка (форма
    auto_send_mail): договоры с начислением, отметки по признаку «Почта» из
    карты, отправка отмеченных с записью в реестр."""
    from . import pochta
    vid = request.GET.get("vid", "schet")
    if vid not in DOKUMENTY:
        raise Http404
    cities = _cities()
    code = _current_city(request, cities)
    city = next((c for c in cities if c.cod_gorod == code), None)
    if city is None:
        raise Http404
    can_send = request.user.has_perm("catalogs.change_potreb")
    if request.method == "POST":
        if not can_send:
            raise PermissionDenied
        problem = pochta.gotovo()
        nomera = [int(x) for x in request.POST.getlist("dog") if x.isdigit()]
        if problem:
            messages.error(request, problem)
        elif not nomera:
            messages.warning(request, "Не отмечено ни одного договора")
        else:
            doks = [d for d in (documents.sobrat(code, n) for n in nomera) if d]
            ctx = _dok_context(doks[0]) if doks else {}
            res = pochta.rassylka(code, nomera, vid, ctx, request.user.get_username())
            ok = sum(1 for z in res if z.status == z.OK)
            (messages.success if ok == len(res) else messages.warning)(
                request, f"Отправлено: {ok} из {len(res)}. Ошибки — в реестре писем.")
        return redirect(f"{reverse('abonents:rassylka')}?gorod={code}&vid={vid}")
    rows = pochta.spisok(code, city.nom_mes, city.god, vid)
    return render(request, "abonents/rassylka.html", {
        "rows": rows, "vid": vid, "vidy": DOKUMENTY.items(), "title": DOKUMENTY[vid], "cities": cities, "city": city,
        "can_send": can_send, "problem": pochta.gotovo(),
    })


@login_required
@view_required
def pisma(request):
    """Реестр отправленных писем (форма reestrmail): фильтр по месяцу и л/№,
    открытие отправленного PDF."""
    from .models import Pismo
    qs = Pismo.objects.all()
    mes = request.GET.get("mes", "")
    if re.fullmatch(r"\d{4}-\d{2}", mes):
        qs = qs.filter(god=int(mes[:4]), nom_mes=int(mes[5:]))
    ls = request.GET.get("ls", "").strip()
    if ls.isdigit():
        qs = qs.filter(Q(potreb_id=int(ls)) | Q(nom_dog=int(ls)))
    if request.GET.get("oshibki"):
        qs = qs.filter(status=Pismo.OSHIBKA)
    page = Paginator(qs, 50).get_page(request.GET.get("page"))
    return render(request, "abonents/pisma.html", {"page": page, "mes": mes, "ls": ls,
                                                   "oshibki": bool(request.GET.get("oshibki")),
                                                   "goroda": dict((c.cod_gorod, c.name_gorod) for c in _cities())})


@login_required
@view_required
def pismo_pdf(request, pk):
    from pathlib import Path
    from .models import Pismo
    z = get_object_or_404(Pismo, pk=pk)
    path = Path(z.fail) if z.fail else None
    if path is None or not path.is_file():
        raise Http404("Файл не найден")
    response = HttpResponse(path.read_bytes(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{path.name}"'
    return response


def _kredo_poluchit(cod_gor, user, xml=None):
    """Получить показания (из сервиса или файла) и сохранить ответ."""
    from . import kredo
    from .models import KredoPriem
    city = Danrasch.objects.get(cod_gorod=cod_gor)
    if not city.nom_mes or not city.god:
        raise kredo.KredoError("У участка не задан текущий месяц")
    istochnik = KredoPriem.FAIL if xml is not None else KredoPriem.KREDO
    if xml is None:
        xml = kredo.zaprosit_pokazaniya(cod_gor, city.nom_mes, city.god)
    rows = kredo.razobrat(xml)
    return KredoPriem.objects.create(user=user, cod_gor=cod_gor, nom_mes=city.nom_mes, god=city.god,
                                     istochnik=istochnik, xml=xml, strok=len(rows))


@login_required
@view_required
def kredo_view(request):
    """Обмен с КРЭДО: приём последних показаний приборов учёта за текущий
    месяц участка (форма rric старой программы)."""
    from . import kredo
    from .models import KredoPriem
    cities = _cities()
    code = _current_city(request, cities)
    city = next((c for c in cities if c.cod_gorod == code), None)
    if city is None:
        raise Http404
    can_change = request.user.has_perm("catalogs.change_potreb")
    if request.method == "POST":
        if not can_change:
            raise PermissionDenied
        try:
            xml = None
            if request.POST.get("action") == "fail":
                f = request.FILES.get("fail")
                if not f:
                    raise kredo.KredoError("Не выбран файл")
                raw = f.read()
                try:
                    xml = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    xml = raw.decode("cp1251")
            z = _kredo_poluchit(code, request.user.get_username(), xml)
        except kredo.KredoError as e:
            messages.error(request, f"КРЭДО: {e}")
            return redirect(f"{reverse('abonents:kredo')}?gorod={code}")
        messages.success(request, f"Информацию о показаниях приборов учета получил: строк {z.strok}")
        return redirect("abonents:kredo_priem", pk=z.pk)
    try:
        nast = kredo.nastrojki(code)
    except kredo.KredoError as e:
        nast = None
        messages.warning(request, str(e))
    return render(request, "abonents/kredo.html", {
        "cities": cities, "city": city, "nast": nast, "can_change": can_change,
        "priemy": KredoPriem.objects.filter(cod_gor=code)[:30],
    })


@login_required
@view_required
def kredo_priem(request, pk):
    """Полученные показания рядом с картами лицевых и их разнос."""
    from . import kredo
    from .models import KredoPriem
    z = get_object_or_404(KredoPriem, pk=pk)
    city = Danrasch.objects.filter(cod_gorod=z.cod_gor).first()
    stroki = kredo.sverit(kredo.razobrat(z.xml))
    tekushchij = city is not None and (city.nom_mes, city.god) == (z.nom_mes, z.god)
    can_change = request.user.has_perm("catalogs.change_potreb") and tekushchij
    if request.method == "POST":
        if not can_change:
            raise PermissionDenied
        nomera = {int(x) for x in request.POST.getlist("n") if x.isdigit()}
        menshe = [s for s in stroki if s.nomer in nomera and s.status == kredo.MENSHE]
        if not nomera:
            messages.warning(request, "Не отмечено ни одной строки")
        elif menshe and not request.POST.get("podtv"):
            messages.error(request, "Текущее показание счетчика не может быть меньше предыдущего: "
                                    "подтвердите разнос таких строк")
        else:
            with transaction.atomic():
                izm = kredo.raznesti(stroki, nomera)
                z.razneseno = timezone.now()
                z.razn_user = request.user.get_username()
                z.izmeneniya = z.izmeneniya + izm
                z.save(update_fields=["razneseno", "razn_user", "izm"])
            messages.success(request, f"Показания приборов учета по лицевым счетам разнесены: {len(izm)}")
        return redirect("abonents:kredo_priem", pk=z.pk)
    from collections import Counter
    return render(request, "abonents/kredo_priem.html", {
        "z": z, "city": city, "stroki": stroki, "can_change": can_change, "tekushchij": tekushchij,
        "itogi": [(t, n) for k, t in kredo.STATUSY.items() if (n := Counter(s.status for s in stroki)[k])],
    })
