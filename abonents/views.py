"""Карта абонента (форма karta старой программы), поиск абонентов и карта
договора (форма karta_dog). Абонент — запись таблицы potreb, в адресах
используется его лицевой № (potreb_id)."""

import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Sum, Value
from django.db.models.functions import Replace
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import formats, timezone

from catalogs.models import Akcept, Bank, Danrasch, GvsKot, Kategorpot, Potreb
from teplo.sqlite_unicode import UnicodeLower

from . import layout
from .forms import karta_form

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

    qs = Potreb.objects.filter(cod_gor=city).select_related("cod_gor").order_by("pk")
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
        "query": params.urlencode(), "filtered": dog is not None or sub is not None or bool(name),
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


def _card_context(request, p, tab_key, form=None):
    related = related_values(p)
    lookups = _lookups()
    _, title, groups = layout.tab(tab_key)
    return {
        "p": p,
        "header": _items(p, layout.HEADER, related, form, lookups),
        "groups": [(g, _items(p, fields, related, form, lookups)) for g, fields in groups],
        "tabs": [(k, t) for k, t, _ in layout.TABS], "tab": tab_key, "tab_title": title,
        "tab_url": reverse("abonents:edit" if form is not None else "abonents:karta", args=[p.potreb_id]),
        "nav": _neighbours(p),
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
