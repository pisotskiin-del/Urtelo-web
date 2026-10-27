"""Загрузка записей из DBF в модели приложения catalogs."""

import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.apps import apps
from django.db import models, transaction
from django.utils import timezone

from .reader import open_dbf

BATCH_SIZE = 1000


class DuplicateKeyError(Exception):
    """В DBF повторяется значение поля, которое в модели помечено unique=True."""


def dbf_models(app_label="catalogs"):
    """Модели с источником DBF, упорядоченные так, что таблица, на которую
    ссылается ForeignKey, идёт раньше ссылающейся."""
    found = [m for m in apps.get_app_config(app_label).get_models() if getattr(m, "dbf_source", "")]
    ordered, seen = [], set()

    def visit(model, path=()):
        if model in seen or model in path:
            return
        for f in model._meta.concrete_fields:
            target = getattr(f, "related_model", None)
            if f.is_relation and target in found and target is not model:
                visit(target, path + (model,))
        seen.add(model)
        ordered.append(model)

    for model in found:
        visit(model)
    return ordered


def column_map(model):
    """{поле модели: имя колонки DBF}. Колонка — dbf_columns, иначе db_column
    поля, иначе его имя (для ForeignKey без db_column это имя без _id)."""
    overrides = getattr(model, "dbf_columns", {}) or {}
    return {
        f: overrides.get(f.name, (f.db_column or f.name).upper())
        for f in model._meta.concrete_fields
        if not f.primary_key
    }


def truncate_tables(models_in_order):
    """Очистить таблицы: сначала ссылающиеся, потом те, на которые ссылаются.
    Удаление без сборщика Django, чтобы on_delete=PROTECT не мешал перезагрузке."""
    for model in reversed(models_in_order):
        model.objects.all()._raw_delete(model.objects.db)


def convert(field, value, encoding="cp1251"):
    if value is None:
        return None
    if field.is_relation:
        # В DBF «нет ссылки» обычно хранится как 0 или пустая строка.
        value = convert(field.target_field, value, encoding)
        return None if value in (0, "") else value
    if isinstance(field, models.DecimalField):
        try:
            return Decimal(str(value)).quantize(Decimal(1).scaleb(-field.decimal_places))
        except (InvalidOperation, ValueError):
            return None
    if isinstance(field, (models.IntegerField, models.BigIntegerField)):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    if isinstance(field, models.DateTimeField):
        if isinstance(value, datetime.datetime):
            return timezone.make_aware(value) if timezone.is_naive(value) else value
        return None
    if isinstance(field, models.DateField):
        return value if isinstance(value, datetime.date) else None
    if isinstance(field, (models.CharField, models.TextField)):
        # Двоичные memo (BinaryMemo) декодируем в кодировке таблицы.
        text = value.decode(encoding, "replace") if isinstance(value, (bytes, bytearray)) else str(value)
        text = text.replace("\x00", "")  # PostgreSQL не принимает нулевые байты в тексте
        if isinstance(field, models.CharField) and field.max_length:
            text = text[: field.max_length]
        return text
    if isinstance(field, models.BinaryField):
        return bytes(value) if isinstance(value, (bytes, bytearray)) else None
    return value


def import_table(model, directory, encoding=None, truncate=True):
    """Перенести одну таблицу. Возвращает (записей в DBF, записей в БД,
    {поле DBF: число нечитаемых значений, заменённых на пустые})."""
    path = _find_file(Path(directory), model.dbf_source)
    table = open_dbf(path, encoding=encoding)
    dbf_names = {f.name.upper() for f in table.fields}
    present = {f: col for f, col in column_map(model).items() if col in dbf_names}

    unique_fields = [f for f in present if f.unique and not f.primary_key]
    seen = {f: {} for f in unique_fields}
    duplicates = []

    source_count = 0
    with transaction.atomic():
        if truncate:
            truncate_tables([model])
        batch = []
        for record in table:  # удалённые записи dbfread пропускает
            source_count += 1
            upper = {k.upper(): v for k, v in record.items()}
            # Признаки NULL в VFP хранятся битами в _NULLFLAGS; переносчик их пока
            # не разбирает, поэтому такие записи только считаем, чтобы их было видно.
            if any(upper.get("_NULLFLAGS") or b""):
                table.parse_errors["_NullFlags"] += 1
            obj = model(**{
                f.attname: convert(f, upper.get(col), table.encoding) for f, col in present.items()
            })
            for f in unique_fields:
                value = getattr(obj, f.attname)
                if value is None:
                    continue
                if value in seen[f]:
                    duplicates.append((present[f], value, seen[f][value], source_count, str(obj)))
                else:
                    seen[f][value] = source_count
            if duplicates:
                continue  # дальше только собираем все повторы, чтобы показать их разом
            batch.append(obj)
            if len(batch) >= BATCH_SIZE and not duplicates:
                model.objects.bulk_create(batch)
                batch = []
        if duplicates:
            lines = [
                f"  {col} = {value!r}: записи №{first} и №{again} ({label})"
                for col, value, first, again, label in duplicates[:20]
            ]
            more = f"\n  … и ещё {len(duplicates) - 20}" if len(duplicates) > 20 else ""
            raise DuplicateKeyError(
                f"{model.dbf_source}: поле должно быть уникальным, но значения повторяются "
                f"(номера среди неудалённых записей):\n" + "\n".join(lines) + more
            )
        if batch:
            model.objects.bulk_create(batch)
    return source_count, model.objects.count(), dict(table.parse_errors)


def _find_file(directory, name):
    """name — путь относительно каталога DBF, например DATA/org.dbf."""
    exact = directory / name
    if exact.exists():
        return exact
    for p in directory.rglob("*"):
        if p.relative_to(directory).as_posix().lower() == name.lower():
            return p
    raise FileNotFoundError(f"{name} не найден в {directory}")
