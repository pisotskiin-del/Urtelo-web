"""Построение моделей Django по заголовкам таблиц DBF.

Результат — исходный код catalogs/models.py. Человеческие названия таблиц
и полей берутся из необязательного файла подписей (labels.json), чтобы
их не приходилось вписывать заново при каждой перегенерации.
"""

import json
import keyword
import re
from dataclasses import dataclass, field
from pathlib import Path

from .dbc import long_names_for
from .reader import find_dbf_files, open_dbf

# Служебное поле VFP со флагами NULL: в модель не переносится.
SKIPPED_TYPES = {"0"}

# Имена, которые нельзя использовать как имя поля модели Django.
RESERVED_NAMES = {"id", "pk", "objects", "dbf_source", "dbf_columns", "save", "delete", "clean"}


@dataclass
class FieldSpec:
    dbf_name: str
    dbf_type: str
    length: int
    decimals: int
    name: str = ""
    label: str = ""
    unique: bool = False
    fk: tuple = None  # (класс модели, поле модели), на которые ссылается поле

    def django_field(self):
        """Тип поля Django и его аргументы (без verbose_name)."""
        t, n, d = self.dbf_type, self.length, self.decimals
        if t in ("C", "V"):
            return "CharField", [f"max_length={max(n, 1)}"]
        if t == "N":
            if d:
                return "DecimalField", [f"max_digits={max(n, d + 1)}", f"decimal_places={d}"]
            return ("IntegerField" if n <= 9 else "BigIntegerField"), []
        if t == "Y":
            return "DecimalField", ["max_digits=19", "decimal_places=4"]
        if t in ("F", "B", "O"):
            return "FloatField", []
        if t in ("I", "+"):
            return "IntegerField", []
        if t == "D":
            return "DateField", []
        if t in ("T", "@"):
            return "DateTimeField", []
        if t == "L":
            return "BooleanField", []
        if t == "M":
            return "TextField", []
        # G, P, W, Q — двоичные данные (OLE, картинки, blob).
        return "BinaryField", []


@dataclass
class TableSpec:
    file_name: str
    class_name: str
    db_table: str
    label: str
    record_count: int
    encoding: str
    fields: list = field(default_factory=list)
    in_dbc: bool = False


def _snake(name):
    name = re.sub(r"[^0-9a-zA-Z_]", "_", name).lower().strip("_")
    name = re.sub(r"_+", "_", name)
    if not name or name[0].isdigit():
        name = "f_" + name
    return name


def _camel(stem):
    parts = re.split(r"[^0-9a-zA-Z]+", stem)
    name = "".join(p[:1].upper() + p[1:].lower() for p in parts if p)
    if not name or name[0].isdigit():
        name = "T" + name
    return name


def field_name_for(dbf_name, taken):
    name = _snake(dbf_name)
    if keyword.iskeyword(name) or name in RESERVED_NAMES:
        name += "_dbf"
    base, i = name, 2
    while name in taken:
        name = f"{base}_{i}"
        i += 1
    taken.add(name)
    return name


def load_labels(path):
    """labels.json: {"ORG": {"title": "Организации", "fields": {"NAME": "Наименование"}}}.
    Ключи — имена таблиц и полей DBF без учёта регистра."""
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    result = {}
    for table, spec in data.items():
        if table.startswith("_"):
            continue
        fields = {k.upper(): v for k, v in (spec.get("fields") or {}).items() if not k.startswith("_")}
        result[table.upper()] = {"title": spec.get("title", ""), "fields": fields}
    return result


def load_relations(path):
    """Файл ключей и связей: {"unique": {"POTREB": ["POTREB_ID"]},
    "foreign_keys": [{"table": "ABONENT", "field": "COD_GOR", "to_table": "GOROD", "to_field": "COD_GOR"}]}."""
    if not path or not Path(path).exists():
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def apply_relations(tables, relations):
    """Убрать таблицы из списка "exclude" и проставить unique и ForeignKey по файлу
    связей. Связи на таблицы и поля, которых нет в каталоге, пропускаются и
    возвращаются списком."""

    def find(table, field):
        t = by_stem.get(table.upper())
        f = next((f for f in t.fields if f.dbf_name == field.upper()), None) if t else None
        return t, f

    excluded = {name.upper() for name in relations.get("exclude") or []}
    tables[:] = [t for t in tables if Path(t.file_name).stem.upper() not in excluded]
    by_stem = {Path(t.file_name).stem.upper(): t for t in tables}

    skipped = []
    for table, fields in (relations.get("unique") or {}).items():
        for name in fields:
            _, f = find(table, name)
            if f:
                f.unique = True
            else:
                skipped.append(f"{table}.{name}")
    for rel in relations.get("foreign_keys") or []:
        _, f = find(rel["table"], rel["field"])
        target, target_field = find(rel["to_table"], rel["to_field"])
        if not f or not target_field:
            skipped.append(f"{rel['table']}.{rel['field']} -> {rel['to_table']}.{rel['to_field']}")
            continue
        target_field.unique = True
        f.fk = (target.class_name, target_field.name)
    return skipped


def inspect_directory(directory, encoding=None, labels=None):
    labels = labels or {}
    directory = Path(directory)
    tables, class_names, db_tables = [], set(), set()
    long_names = long_names_for(directory)
    for path in find_dbf_files(directory):
        table = open_dbf(path, encoding=encoding)
        stem = path.stem
        table_labels = labels.get(stem.upper(), {})
        class_name = _camel(stem)
        base, i = class_name, 2
        # Django различает модели по имени без учёта регистра (polez_otpusk и polezotpusk).
        while class_name.lower() in class_names:
            class_name = f"{base}{i}"
            i += 1
        class_names.add(class_name.lower())
        db_table = _snake(stem)
        base, i = db_table, 2
        while db_table in db_tables:
            db_table = f"{base}_{i}"
            i += 1
        db_tables.add(db_table)

        spec = TableSpec(
            file_name=path.relative_to(directory).as_posix(),
            class_name=class_name,
            db_table=db_table,
            label=table_labels.get("title") or stem.upper(),
            record_count=len(table),
            encoding=table.encoding,
        )
        spec.in_dbc = stem.lower() in long_names
        full = {n.lower()[:10]: n for n in long_names.get(stem.lower(), [])}
        taken = set()
        for f in table.fields:
            if f.type in SKIPPED_TYPES or f.name.startswith("_"):
                continue
            fs = FieldSpec(f.name.upper(), f.type, f.length, f.decimal_count)
            fs.name = field_name_for(full.get(f.name.lower(), f.name), taken)
            fs.label = table_labels.get("fields", {}).get(fs.dbf_name) or fs.dbf_name
            spec.fields.append(fs)
        tables.append(spec)
    return tables


def _q(text):
    return json.dumps(text, ensure_ascii=False)


def render_models(tables, source_dir=""):
    out = [
        '"""Модели справочников и таблиц старой программы.',
        "",
        "Файл сгенерирован командой `python manage.py dbf_inspect`",
        f"по таблицам из {source_dir or 'каталога DBF'}.",
        "Не правьте его вручную: названия таблиц и полей задаются в",
        "dbfsync/labels/ur_teplo.json, ключи и связи — в ur_teplo_relations.json.",
        '"""',
        "",
        "from django.db import models",
        "",
        "",
        "class DbfModel(models.Model):",
        '    """Общий предок: хранит имя исходного файла DBF и соответствие полей."""',
        "",
        '    dbf_source = ""',
        "    dbf_columns = {}",
        "",
        "    class Meta:",
        "        abstract = True",
        "",
        "    def __str__(self):",
        "        for f in self._meta.concrete_fields:",
        '            if f.get_internal_type() == "CharField":',
        "                value = getattr(self, f.attname)",
        "                if value:",
        "                    return str(value)",
        '        return f"{self._meta.verbose_name} #{self.pk}"',
    ]
    for t in tables:
        out += ["", "", f"class {t.class_name}(DbfModel):"]
        where = "таблица базы" if t.in_dbc else "свободная таблица"
        out.append(f'    """{t.file_name} ({where}): записей {t.record_count}, кодировка {t.encoding}."""')
        out.append("")
        out.append(f"    dbf_source = {_q(t.file_name)}")
        renamed = {f.name: f.dbf_name for f in t.fields if f.name.upper() != f.dbf_name}
        if renamed:
            out.append(f"    dbf_columns = {_q(renamed)}")
        out.append("")
        for f in t.fields:
            if f.fk:
                to_class, to_field = f.fk
                args = [_q(to_class), "models.PROTECT", f"verbose_name={_q(f.label)}",
                        f"to_field={_q(to_field)}", f"db_column={_q(f.name)}", "null=True", "blank=True"]
                out.append(f"    {f.name} = models.ForeignKey({', '.join(args)})")
                continue
            ftype, args = f.django_field()
            args = [_q(f.label)] + args
            if f.unique:
                args.append("unique=True")
            if ftype == "BooleanField":
                args.append("null=True")
            elif ftype == "BinaryField":
                args += ["null=True", "blank=True", "editable=False"]
            else:
                args += ["null=True", "blank=True"]
            out.append(f"    {f.name} = models.{ftype}({', '.join(args)})")
        out += [
            "",
            "    class Meta:",
            f"        db_table = {_q(t.db_table)}",
            f"        verbose_name = {_q(t.label)}",
            f"        verbose_name_plural = {_q(t.label)}",
            "        ordering = [\"pk\"]",
        ]
    out.append("")
    return "\n".join(out)
