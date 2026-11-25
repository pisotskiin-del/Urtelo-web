import io
import tempfile
import time
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError, call_command
from django.core.paginator import Paginator
from django.db.models import Q
from django.forms import Textarea, modelform_factory
from django.shortcuts import get_object_or_404, redirect, render

from accounts.roles import is_admin
from dbfsync.importer import copy_sources, dbf_models
from dbfsync.management.commands.dbf_import import Command as DbfImport
from teplo.sqlite_unicode import UnicodeLower

from .registry import catalog_models, data_fields, get_model, list_fields, search_fields


def _value(obj, f):
    """Значение поля; для поля со списком выбора — его подпись."""
    if f.choices:
        return getattr(obj, f"get_{f.name}_display")()
    return getattr(obj, f.name)


def _perm(user, model, action):
    return user.has_perm(f"{model._meta.app_label}.{action}_{model._meta.model_name}")


def _require(user, model, action):
    if not _perm(user, model, action):
        raise PermissionDenied


@login_required
def index(request):
    items = [
        {"slug": m._meta.model_name, "title": m._meta.verbose_name_plural,
         "source": getattr(m, "dbf_source", "веб-программа"), "count": m.objects.count()}
        for m in catalog_models() if _perm(request.user, m, "view")
    ]
    return render(request, "catalogs/index.html", {"items": items, "can_update": is_admin(request.user)})


DBF_APP = "catalogs"  # приложение с моделями DBF; в тестах — dbfsync_testapp


@login_required
def dbf_update(request):
    """Обновить справочники из DBF старой программы (то же, что manage.py dbf_import):
    таблицы копируются во временную папку, очищаются и загружаются заново, число
    записей сверяется с DBF. При любой ошибке база остаётся как была."""
    if not is_admin(request.user):
        raise PermissionDenied
    targets = dbf_models(DBF_APP)
    folder = (request.POST.get("folder") or settings.DBF_SOURCE_DIR).strip()
    ctx = {"folder": folder, "tables": len(targets), "result": None}
    if request.method == "POST":
        if not request.POST.get("confirm"):
            ctx["error"] = "Отметьте флажок, что вы понимаете: данные справочников будут заменены."
        elif not Path(folder).is_dir():
            ctx["error"] = f"Папка {folder} не найдена."
        else:
            ctx["result"] = _run_dbf_import(targets, folder)
            if ctx["result"]["ok"]:
                messages.success(request, f"Данные обновлены из {folder}: загружено таблиц "
                                          f"{len(ctx['result']['rows'])}, записей {ctx['result']['total']}.")
            else:
                messages.error(request, "Обновление не выполнено, данные в базе не изменены. Причины ниже.")
    return render(request, "catalogs/dbf_update.html", ctx)


def _run_dbf_import(targets, folder):
    started = time.monotonic()
    log = io.StringIO()
    command = DbfImport(stdout=log, stderr=log, no_color=True)
    command.rows, command.errors = [], []
    ok = False
    with tempfile.TemporaryDirectory(prefix="teplo_dbf_") as copy:
        files, size, missing = copy_sources(targets, folder, copy)
        if missing:  # не загружаем вовсе, иначе пришлось бы откатывать
            command.errors.append(f"В папке {folder} нет таблиц ({len(missing)} из {len(targets)}): "
                                  + ", ".join(missing))
        else:
            try:
                call_command(command, dir=copy, app=DBF_APP)
                ok = True
            except CommandError as exc:
                if not command.errors and all(r["ok"] for r in command.rows):
                    command.errors.append(str(exc))
            command.errors = [e.replace(copy, folder) for e in command.errors]
    rows = command.rows
    return {
        "ok": ok, "rows": rows, "errors": command.errors,
        "bad": [r for r in rows if not r["ok"]],
        "total": sum(r["db"] for r in rows), "files": files, "size_mb": round(size / 2**20, 1),
        "seconds": round(time.monotonic() - started),
    }


@login_required
def object_list(request, slug):
    model = get_model(slug)
    _require(request.user, model, "view")
    columns = list_fields(model)
    qs = model.objects.all()

    query = request.GET.get("q", "").strip()
    if query:
        cond = Q()
        for i, f in enumerate(search_fields(model)):
            qs = qs.alias(**{f"_search{i}": UnicodeLower(f.name)})
            cond |= Q(**{f"_search{i}__contains": query.lower()})
        qs = qs.filter(cond)

    sort = request.GET.get("o", "")
    if sort.lstrip("-") in {f.name for f in columns}:
        qs = qs.order_by(sort, "pk")

    headers = []
    for f in columns:
        if sort == f.name:
            headers.append((f.verbose_name, "-" + f.name, "▲"))
        elif sort == "-" + f.name:
            headers.append((f.verbose_name, f.name, "▼"))
        else:
            headers.append((f.verbose_name, f.name, ""))

    page = Paginator(qs, settings.CATALOG_PAGE_SIZE).get_page(request.GET.get("page"))
    rows = [(obj, [_value(obj, f) for f in columns]) for obj in page]
    return render(request, "catalogs/list.html", {
        "meta": model._meta, "slug": slug, "headers": headers,
        "rows": rows, "page": page, "query": query, "sort": sort,
        "can_add": _perm(request.user, model, "add"),
    })


@login_required
def object_detail(request, slug, pk):
    model = get_model(slug)
    _require(request.user, model, "view")
    obj = get_object_or_404(model, pk=pk)
    values = [
        (f.verbose_name, _value(obj, f), f.get_internal_type() == "TextField")
        for f in data_fields(model)
    ]
    return render(request, "catalogs/detail.html", {
        "meta": model._meta, "slug": slug, "obj": obj, "values": values,
        "can_change": _perm(request.user, model, "change"),
        "can_delete": _perm(request.user, model, "delete"),
    })


@login_required
def object_edit(request, slug, pk=None):
    model = get_model(slug)
    obj = get_object_or_404(model, pk=pk) if pk else None
    _require(request.user, model, "change" if obj else "add")
    fields = data_fields(model)
    # Длинные строки (должность подписанта и т.п.) — в поле в две строки,
    # чтобы надпись была видна целиком.
    widgets = {f.name: Textarea(attrs={"rows": 2}) for f in fields
               if f.get_internal_type() == "CharField" and (f.max_length or 0) >= 100}
    form_class = modelform_factory(model, fields=[f.name for f in fields], widgets=widgets)
    form = form_class(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, "Запись сохранена")
        return redirect("catalogs:detail", slug=slug, pk=obj.pk)
    return render(request, "catalogs/form.html", {"meta": model._meta, "slug": slug, "obj": obj, "form": form})


@login_required
def object_delete(request, slug, pk):
    model = get_model(slug)
    _require(request.user, model, "delete")
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Запись удалена")
        return redirect("catalogs:list", slug=slug)
    return render(request, "catalogs/confirm_delete.html", {"meta": model._meta, "slug": slug, "obj": obj})
