#!/usr/bin/env python3
"""Перенос таблиц Visual FoxPro (.dbf) в PostgreSQL веб-приложения Urteplo.

Схемой БД владеют модели Django (catalogs/models.py, их строит `manage.py dbf_inspect`),
таблицы создаёт `manage.py migrate`. Этот инструмент только наполняет их и проверяет:

  analyze  кодировки, первичные ключи и связи между таблицами -> report.json и report.md
           (в report.md готовые строки ForeignKey для catalogs/models.py)
  load     перенос через COPY; таблицы перед загрузкой очищаются
  verify   сверка: число записей, непустые значения, суммы чисел, контрольные суммы текста
  all      analyze + load + verify

Какой файл в какую таблицу и какое поле в какую колонку, берётся из catalogs/models.py
(--models: dbf_source, dbf_columns, Meta.db_table, db_column). Без --models имена
вычисляются по тем же правилам, что в dbfsync/schema.py.
Суррогатный id заполняет PostgreSQL, в порядке записей DBF.

Пример:
  python dbf2pg.py all --src D:/copy_teplo_dog --models catalogs/models.py \\
      --dsn "host=localhost dbname=teplo user=postgres password=..."
"""
import argparse
import ast
import datetime as dt
import decimal
import hashlib
import json
import keyword
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path

from dbfread import DBF, FieldParser
from dbfread.memo import BinaryMemo

log = logging.getLogger("dbf2pg")


# --------------------------------------------------------------------------- имена

RESERVED_NAMES = {"id", "pk", "objects", "dbf_source", "dbf_columns", "save", "delete", "clean"}


def snake(name):
    name = re.sub(r"[^0-9a-zA-Z_]", "_", name).lower().strip("_")
    name = re.sub(r"_+", "_", name)
    if not name or name[0].isdigit():
        name = "f_" + name
    return name


def column_name_for(dbf_name, taken):
    name = snake(dbf_name)
    if keyword.iskeyword(name) or name in RESERVED_NAMES:
        name += "_dbf"
    base, i = name, 2
    while name in taken:
        name = f"{base}_{i}"
        i += 1
    taken.add(name)
    return name


def read_models(path):
    """Из catalogs/models.py: {dbf_source в нижнем регистре: {"table": db_table, "columns": {ПОЛЕ_DBF: колонка}}}.
    Файл разбирается как текст (ast), Django для этого не нужен."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    result = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        source, renamed, table, fields = "", {}, None, {}
        for st in cls.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                name, value = st.targets[0].id, st.value
                if name == "dbf_source":
                    source = ast.literal_eval(value)
                elif name == "dbf_columns":
                    renamed = ast.literal_eval(value)
                elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
                    kw = {k.arg: k.value for k in value.keywords}
                    if "db_column" in kw:
                        column = ast.literal_eval(kw["db_column"])
                    elif value.func.attr in ("ForeignKey", "OneToOneField"):
                        column = name + "_id"
                    else:
                        column = name
                    fields[name] = column
            elif isinstance(st, ast.ClassDef) and st.name == "Meta":
                for m in st.body:
                    if isinstance(m, ast.Assign) and getattr(m.targets[0], "id", "") == "db_table":
                        table = ast.literal_eval(m.value)
        if source:
            table = table or f"catalogs_{cls.name.lower()}"
            columns = {renamed.get(f, f.upper()).upper(): col for f, col in fields.items()}
            result[source.replace("\\", "/").lower()] = {"table": table, "columns": columns, "model": cls.name}
    return result


# --------------------------------------------------------------------------- чтение DBF

class TolerantParser(FieldParser):
    """Не падает на битых значениях: пишет их в счётчик и возвращает None.
    Числа с дробной частью читаются как Decimal, чтобы не терять копейки."""

    bad_values = defaultdict(int)

    def _bad(self, field):
        TolerantParser.bad_values[(Path(self.table.filename).name, field.name)] += 1
        return None

    def parse(self, field, data):
        try:
            return super().parse(field, data)
        except (ValueError, UnicodeDecodeError, IndexError, KeyError):
            return self._bad(field)

    def parseN(self, field, data):
        data = data.strip().strip(b"*").replace(b",", b".")
        if not data:
            return None
        try:
            return decimal.Decimal(data.decode("ascii")) if field.decimal_count else int(data)
        except (ValueError, decimal.InvalidOperation, UnicodeDecodeError):
            try:
                return decimal.Decimal(data.decode("ascii"))
            except (ValueError, decimal.InvalidOperation, UnicodeDecodeError):
                return self._bad(field)

    def parseV(self, field, data):
        return self.decode_text(data.rstrip(b"\0 "))

    def parseQ(self, field, data):
        return bytes(data)

    def parseW(self, field, data):
        return self.get_memo(self._parse_memo_index(data))


CYR = re.compile("[А-Яа-яЁё]")


def guess_encoding(path, forced=None):
    """Кодировка из заголовка DBF. Если там 0 (dbfread тогда берёт ascii и молча
    портит кириллицу), выбираем cp866 или cp1251 по числу русских букв в тексте."""
    if forced:
        return forced, "задана вручную"
    probe = DBF(path, load=False, ignore_missing_memofile=True)
    if probe.encoding not in ("ascii", None):
        return probe.encoding, "из заголовка"
    raw = DBF(path, raw=True, ignore_missing_memofile=True)
    char_fields = [f.name for f in raw.fields if f.type in "CV"]
    sample = bytearray()
    for i, rec in enumerate(raw):
        for name in char_fields:
            sample += rec[name] or b""
        if i > 2000 or len(sample) > 200_000:
            break
    if not any(b >= 0x80 for b in sample):
        return "cp866", "в заголовке нет, русского текста нет"
    scores = {enc: len(CYR.findall(bytes(sample).decode(enc, "replace"))) for enc in ("cp866", "cp1251")}
    return max(scores, key=scores.get), f"в заголовке нет, по тексту {scores}"


def open_dbf(path, encoding):
    return DBF(path, encoding=encoding, parserclass=TolerantParser, char_decode_errors="replace",
               ignore_missing_memofile=True)


def find_dbfs(src):
    return sorted((p for p in Path(src).rglob("*") if p.is_file() and p.suffix.lower() == ".dbf"),
                  key=lambda p: str(p).lower())


def dbf_tables(src, encoding=None, models=None, exclude=()):
    """Описание всех таблиц: файл, таблица в PostgreSQL, кодировка, поля -> колонки."""
    result = {}
    exclude = {x.strip().lower() for x in exclude if x.strip()}
    for path in find_dbfs(src):
        rel = path.relative_to(src).as_posix().lower()
        if rel in exclude or path.name.lower() in exclude or rel.split("/")[0] in exclude:
            log.info("%s: исключён (--exclude)", rel)
            continue
        model = (models or {}).get(rel) or (models or {}).get(path.name.lower())
        if models is not None and not model:
            log.warning("%s: нет модели в models.py, файл пропущен", rel)
            continue
        name = model["table"] if model else snake(path.stem)
        base, i = name, 2
        while name in result:
            if model:
                log.warning("таблица %s указана для двух файлов, %s пропущен", name, rel)
                break
            name = f"{base}_{i}"
            i += 1
        else:
            enc, how = guess_encoding(path, encoding)
            dbf = open_dbf(path, enc)
            taken, fields = set(), []
            for f in dbf.fields:
                if f.type == "0" or f.name.startswith("_"):  # _NullFlags и служебные поля
                    continue
                if model:
                    column = model["columns"].get(f.name.upper())
                    if not column:
                        log.warning("%s: поля %s нет в модели %s", rel, f.name, model["model"])
                        continue
                else:
                    column = column_name_for(f.name, taken)
                fields.append({"dbf": f.name, "column": column, "type": f.type,
                               "length": f.length, "decimals": f.decimal_count})
            result[name] = {"file": str(path), "rel": path.relative_to(src).as_posix(), "model": model["model"] if model else camel(path.stem),
                            "encoding": enc, "encoding_how": how, "fields": fields,
                            "records": len(dbf.records), "deleted": len(dbf.deleted)}
    return result


def camel(stem):
    parts = re.split(r"[^0-9a-zA-Z]+", stem)
    name = "".join(p[:1].upper() + p[1:].lower() for p in parts if p)
    return name if name and not name[0].isdigit() else "T" + name


# --------------------------------------------------------------------------- анализ ключей и связей

KEY_NAME_PATTERNS = [r"^id$", r"^kod$", r"^code$", r"^id_?\w+$", r"^\w+_?id$", r"^kod_?\w+$", r"^\w+_?kod$",
                     r"^n_?\w+$", r"^nom\w*$"]
KEYABLE = set("CVNI+")


def key_rank(name, table):
    """Чем меньше, тем больше поле похоже на ключ таблицы. Имя с названием таблицы
    (n_dog в dogovor, id_abon в abonent) важнее общего kod, который часто ссылка."""
    name = name.lower()
    for i, pat in enumerate(KEY_NAME_PATTERNS):
        if re.match(pat, name):
            own = re.sub(r"^(id|kod|code|n|nom)_?|_?(id|kod)$", "", name) in (table, table[:3], table[:4])
            return -1 if own and name not in ("id", "kod", "code") else i
    return len(KEY_NAME_PATTERNS)


def is_empty(v):
    return v is None or v == "" or (v == 0 and not isinstance(v, bool))


def read_dbc_keys(path):
    """Индексы из словаря базы VFP (.dbc): там записаны первичные и потенциальные ключи.
    {таблица: [имя тега]}; имя тега обычно совпадает с именем поля."""
    path = Path(path)
    memo = path.with_suffix(".dct")
    if not memo.exists():
        memo = next((p for p in path.parent.iterdir() if p.name.lower() == path.stem.lower() + ".dct"), memo)
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:  # dbfread ищет memo в .fpt, а у .dbc он в .dct
        shutil.copy(path, Path(tmp) / "dbc.dbf")
        shutil.copy(memo, Path(tmp) / "dbc.fpt")
        recs = list(DBF(Path(tmp) / "dbc.dbf", encoding="cp1251", char_decode_errors="replace"))
    names = {r["OBJECTID"]: r["OBJECTNAME"].strip().lower() for r in recs}
    keys = defaultdict(list)
    for r in recs:
        if r["OBJECTTYPE"].strip() == "Index":
            keys[names.get(r["PARENTID"], "")].append(r["OBJECTNAME"].strip().lower())
    return dict(keys)


def analyze(tables, dbc_keys=None, manual_links=()):
    """Ключ таблицы выбирается так: индекс из .dbc, затем поле с именем таблицы (n_dog в dogovor),
    затем уникальное поле, похожее на ключ по имени, но не ключ другой таблицы (это ссылка)."""
    dbc_keys = dbc_keys or {}
    values, cands_by_table = {}, {}
    for name, t in tables.items():
        dbf = open_dbf(t["file"], t["encoding"])
        keyable = [f for f in t["fields"] if f["type"] in KEYABLE and not (f["type"] == "N" and f["decimals"])]
        seen = {f["dbf"]: set() for f in keyable}
        unique = {f["dbf"]: True for f in keyable}
        for rec in dbf.records:
            for f in keyable:
                v = rec.get(f["dbf"])
                if v is None or v == "" or v in seen[f["dbf"]]:
                    unique[f["dbf"]] = False
                if v is not None and v != "":
                    seen[f["dbf"]].add(v)
        cands = [f for f in keyable if unique[f["dbf"]] and t["records"]]
        cands.sort(key=lambda f: key_rank(f["dbf"], name))
        cands_by_table[name] = cands
        t["unique_columns"] = [f["column"] for f in cands]
        t["links"], t["weak_links"] = [], []
        for f in keyable:
            values[(name, f["column"])] = seen[f["dbf"]]
        t["key"], t["key_source"] = None, None
        dbc_name = Path(t["file"]).stem.lower()
        for tag in dbc_keys.get(dbc_name, []):
            f = next((f for f in cands if f["dbf"].lower() == tag), None)
            if f:
                t["key"], t["key_source"] = f["column"], "индекс в .dbc"
                break
        if not t["key"] and cands and key_rank(cands[0]["dbf"], name) < 0:
            t["key"], t["key_source"] = cands[0]["column"], "имя поля"

    strong = {t["key"] for t in tables.values() if t["key"]}
    for name, t in tables.items():
        if t["key"]:
            continue
        for f in cands_by_table[name]:
            if key_rank(f["dbf"], name) < len(KEY_NAME_PATTERNS) and f["column"] not in strong:
                t["key"], t["key_source"] = f["column"], "уникальные значения"
                break
    for name, t in tables.items():
        log.info("%-20s %7d записей (+%d удалённых)  %-6s %s  ключ: %s", name, t["records"], t["deleted"],
                 t["encoding"], t["encoding_how"], f'{t["key"]} ({t["key_source"]})' if t["key"] else "не найден")

    # Связи, заданные вручную (--link potreb.cod_gor=danrasch.cod_gorod), важнее найденных по именам
    manual = {}
    for spec in manual_links:
        left, right = spec.lower().split("=")
        b, c = left.split(".")
        a, k = right.split(".")
        sources = [n for n in tables if n != a and (n, c) in values] if b == "*" else [b]
        if a not in tables or any(n not in tables for n in sources):
            log.warning("--link %s: таблицы нет", spec)
            continue
        if tables[a]["key"] != k:
            tables[a]["key"], tables[a]["key_source"] = k, "задан вручную"
        for n in sources:
            manual[(n, c)] = (a, k)
    for (b, c), (a, k) in manual.items():
        b_vals = {v for v in values.get((b, c), ()) if not is_empty(v)}
        orphans = b_vals - values.get((a, k), set())
        link = {"column": c, "ref_table": a, "ref_column": k, "manual": True}
        if orphans:
            tables[b]["weak_links"].append({**link, "orphans": len(orphans),
                                            "examples": sorted(str(x) for x in orphans)[:5]})
            log.warning("связь %s.%s -> %s.%s (вручную): %d значений без пары", b, c, a, k, len(orphans))
        else:
            tables[b]["links"].append(link)
            log.info("связь %s.%s -> %s.%s (вручную)", b, c, a, k)

    for b, tb in tables.items():
        for f in tb["fields"]:
            c = f["column"]
            if (b, c) in manual:
                continue
            if c == tb["key"] or (b, c) not in values or c in ("id", "kod", "code", "name"):
                continue  # общие имена вроде kod в каждой таблице свои, это не ссылка
            b_vals = {v for v in values[(b, c)] if not is_empty(v)}
            for a, ta in tables.items():
                k = ta["key"]
                if a == b or not k or not b_vals or not values[(a, k)]:
                    continue
                if ta["key_source"] == "уникальные значения":
                    continue  # ссылаться можно только на надёжный ключ: из .dbc или по имени таблицы
                names = {k, f"{k}_{a}", f"{a}_{k}", f"id_{a}", f"{a}_id", f"kod_{a}", f"{a}_kod"}
                if c not in names or isinstance(next(iter(b_vals)), str) != isinstance(next(iter(values[(a, k)])), str):
                    continue
                orphans = b_vals - values[(a, k)]
                link = {"column": c, "ref_table": a, "ref_column": k}
                if not orphans:
                    tb["links"].append(link)
                    log.info("связь %s.%s -> %s.%s", b, c, a, k)
                elif len(orphans) <= max(2, len(b_vals) // 5):  # больше 20% без пары: совпали только имена
                    tb["weak_links"].append({**link, "orphans": len(orphans),
                                             "examples": sorted(str(x) for x in orphans)[:5]})
                    log.warning("связь %s.%s -> %s.%s: %d значений без пары, внешний ключ не рекомендуется",
                                b, c, a, k, len(orphans))
    return tables


def write_report(tables, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(tables, ensure_ascii=False, indent=2, default=str),
                                         encoding="utf-8")
    md = ["# Таблицы DBF: ключи и связи", "",
          "| Таблица | Файл | Записей | Удалено | Кодировка | Ключ (откуда) |", "|---|---|---|---|---|---|"]
    for name, t in tables.items():
        md.append(f"| {name} | {t['rel']} | {t['records']} | {t['deleted']} | {t['encoding']} "
                  f"({t['encoding_how']}) | {t['key'] or '—'}{' (' + t['key_source'] + ')' if t['key'] else ''} |")
    md += ["", "## Что поправить в catalogs/models.py", "",
           "Ключевым полям нужен `unique=True`, полям-ссылкам `ForeignKey` с `to_field` и `db_column`, "
           "чтобы колонка в базе осталась той же. При загрузке 0 и пустая строка в полях-ссылках станут NULL.", ""]
    referenced = {l["ref_table"] for t in tables.values() for l in t["links"]}
    for name in sorted(referenced):
        md.append(f"- `{tables[name]['model']}.{tables[name]['key']}`: добавить `unique=True`")
    for name, t in tables.items():
        many = defaultdict(int)
        for l in t["links"]:
            many[l["column"]] += 1
        for l in t["links"]:
            note = " (найдено несколько таблиц, оставьте одну)" if many[l["column"]] > 1 else ""
            md.append(f"- `{t['model']}.{l['column']} = models.ForeignKey(\"{tables[l['ref_table']]['model']}\", "
                      f"to_field=\"{l['ref_column']}\", db_column=\"{l['column']}\", null=True, blank=True, "
                      f"on_delete=models.PROTECT)`{note}")
    if not referenced:
        md.append("Надёжных связей не найдено.")
    weak = [(n, l) for n, t in tables.items() for l in t["weak_links"]]
    if weak:
        md += ["", "## Похоже на связь, но есть значения без пары", ""]
        for n, l in weak:
            md.append(f"- {n}.{l['column']} -> {l['ref_table']}.{l['ref_column']}: {l['orphans']} без пары, "
                      f"например {', '.join(l['examples'])}")
    (out_dir / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    # Тот же список в формате dbfsync (dbfsync/labels/ur_teplo_relations.json), чтобы dbf_inspect
    # сам проставил unique и ForeignKey в catalogs/models.py
    stem = {n: Path(t["file"]).stem.upper() for n, t in tables.items()}
    dbf_name = {(n, f["column"]): f["dbf"].upper() for n, t in tables.items() for f in t["fields"]}
    relations = {"unique": defaultdict(list), "foreign_keys": []}
    for name, t in tables.items():
        for l in t["links"]:
            ref, to = l["ref_table"], dbf_name[(l["ref_table"], l["ref_column"])]
            if to not in relations["unique"][stem[ref]]:
                relations["unique"][stem[ref]].append(to)
            relations["foreign_keys"].append({"table": stem[name], "field": dbf_name[(name, l["column"])],
                                              "to_table": stem[ref], "to_field": to})
    (out_dir / "relations.json").write_text(json.dumps(relations, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("отчёт: %s", out_dir / "report.md")


# --------------------------------------------------------------------------- перенос

def pg_columns(conn, table):
    rows = conn.execute(
        "SELECT column_name, data_type, character_maximum_length FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = %s", (table,)).fetchall()
    return {r[0]: {"type": r[1], "maxlen": r[2]} for r in rows}


def pg_foreign_keys(conn, table):
    """{колонка: таблица, на которую она ссылается}."""
    rows = conn.execute(
        "SELECT a.attname, c.confrelid::regclass::text FROM pg_constraint c "
        "JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) "
        "WHERE c.contype = 'f' AND c.conrelid = to_regclass(%s)", (f'"{table}"',)).fetchall()
    return {r[0]: r[1].strip('"') for r in rows}


def plan(conn, tables):
    """Какие колонки DBF куда грузить, и порядок таблиц: сначала те, на которые ссылаются."""
    result = {}
    for name, t in tables.items():
        cols = pg_columns(conn, name)
        if not cols:
            log.warning("%s: таблицы нет в PostgreSQL (не выполнен migrate?), пропущена", name)
            continue
        missing = [f["dbf"] for f in t["fields"] if f["column"] not in cols]
        if missing:
            log.warning("%s: в PostgreSQL нет колонок для полей %s", name, ", ".join(missing))
        result[name] = {**t, "fields": [f for f in t["fields"] if f["column"] in cols], "pg": cols,
                        "fk": pg_foreign_keys(conn, name)}
    order, done = [], set()

    def visit(n, path=()):
        if n in done or n in path or n not in result:
            return
        for ref in result[n]["fk"].values():
            visit(ref, path + (n,))
        done.add(n)
        order.append(n)

    for n in result:
        visit(n)
    return result, order


truncated = defaultdict(int)


def rows(t):
    """Значения для COPY в порядке t["fields"] и в порядке записей DBF (удалённые пропускаются)."""
    dbf = open_dbf(t["file"], t["encoding"])
    spec = [(f["dbf"], t["pg"][f["column"]]["type"], t["pg"][f["column"]]["maxlen"], f["column"] in t["fk"])
            for f in t["fields"]]
    for rec in dbf.records:
        out = []
        for dbf_name, pgtype, maxlen, is_fk in spec:
            v = rec.get(dbf_name)
            if isinstance(v, BinaryMemo):
                v = bytes(v)
            if isinstance(v, bytes) and pgtype != "bytea":
                v = v.decode(t["encoding"], "replace")
            elif isinstance(v, str) and pgtype == "bytea":
                v = v.encode(t["encoding"], "replace")
            if isinstance(v, str):
                v = v.replace("\x00", "")  # PostgreSQL не хранит нулевые байты в тексте
                if maxlen and len(v) > maxlen:
                    truncated[(Path(t["file"]).name, dbf_name)] += 1
                    v = v[:maxlen]
            if is_fk and is_empty(v):  # в FoxPro 0 и пустая строка значат «нет ссылки»
                v = None
            if pgtype.startswith("timestamp") and isinstance(v, dt.date) and not isinstance(v, dt.datetime):
                v = dt.datetime.combine(v, dt.time())
            out.append(v)
        yield out


def load(conn, p, order):
    TolerantParser.bad_values.clear()
    truncated.clear()
    with conn.transaction():
        conn.execute("TRUNCATE " + ", ".join(f'"{n}"' for n in order) + " RESTART IDENTITY CASCADE")
        for name in order:
            t = p[name]
            cols = ", ".join(f'"{f["column"]}"' for f in t["fields"])
            n = 0
            with conn.cursor().copy(f'COPY "{name}" ({cols}) FROM STDIN') as copy:
                for row in rows(t):
                    copy.write_row(row)
                    n += 1
            log.info("%-20s загружено %7d", name, n)
    for title, counter in (("битые значения заменены на NULL", TolerantParser.bad_values),
                           ("текст обрезан по длине колонки", truncated)):
        if counter:
            log.warning("%s:", title)
            for (f, col), cnt in sorted(counter.items()):
                log.warning("  %s.%s: %d", f, col, cnt)


# --------------------------------------------------------------------------- сверка

def verify(conn, p, order):
    """Сверка по каждой таблице: записи, непустые значения, суммы чисел, md5 текста по порядку id."""
    problems = []
    for name in order:
        t = p[name]
        cols = [f["column"] for f in t["fields"]]
        types = [t["pg"][c]["type"] for c in cols]
        num = {i for i, ty in enumerate(types) if ty in ("integer", "bigint", "smallint", "numeric")}
        txt = {i for i, ty in enumerate(types) if ty in ("character varying", "text")}
        count, nonnull = 0, [0] * len(cols)
        sums = {i: decimal.Decimal(0) for i in num}
        texts = {i: [] for i in txt}
        for row in rows(t):
            count += 1
            for i, v in enumerate(row):
                if v is not None:
                    nonnull[i] += 1
                    if i in sums:
                        sums[i] += decimal.Decimal(v)
                if i in texts:
                    texts[i].append(v or "")
        got = conn.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
        if got != count:
            problems.append(f"{name}: записей в DBF {count}, в PostgreSQL {got}")
        exprs = []
        for i, c in enumerate(cols):
            exprs.append(f'count("{c}")')
            if i in sums:
                exprs.append(f'coalesce(sum("{c}"), 0)')
            if i in texts:
                exprs.append(f"md5(coalesce(string_agg(coalesce(\"{c}\", ''), E'\\x1f' ORDER BY id), ''))")
        res = list(conn.execute(f'SELECT {", ".join(exprs)} FROM "{name}"').fetchone()) if exprs else []
        bad = 0
        for i, c in enumerate(cols):
            got_nonnull = res.pop(0)
            if got_nonnull != nonnull[i]:
                problems.append(f"{name}.{c}: непустых в DBF {nonnull[i]}, в PostgreSQL {got_nonnull}")
                bad += 1
            if i in sums:
                got_sum = decimal.Decimal(res.pop(0))
                if got_sum != sums[i]:
                    problems.append(f"{name}.{c}: сумма в DBF {sums[i]}, в PostgreSQL {got_sum}")
                    bad += 1
            if i in texts and res.pop(0) != hashlib.md5("\x1f".join(texts[i]).encode("utf-8")).hexdigest():
                problems.append(f"{name}.{c}: текст отличается")
                bad += 1
        log.info("%-20s DBF %7d  PostgreSQL %7d  %s", name, count, got,
                 "OK" if got == count and not bad else "РАСХОЖДЕНИЕ")
    if problems:
        log.error("найдены расхождения:")
        for x in problems:
            log.error("  %s", x)
        return False
    log.info("все %d таблиц совпадают: записи, непустые значения, суммы, текст", len(order))
    return True


# --------------------------------------------------------------------------- командная строка

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["analyze", "load", "verify", "all"])
    ap.add_argument("--src", required=True, help="папка с копией .dbf")
    ap.add_argument("--models", help="catalogs/models.py: откуда брать имена таблиц и колонок")
    ap.add_argument("--dsn", help='строка подключения: "host=localhost dbname=teplo user=postgres password=..."')
    ap.add_argument("--encoding", help="принудительная кодировка для всех таблиц (cp866 или cp1251)")
    ap.add_argument("--exclude", default="", help="не переносить: файлы или папки через запятую, например sul.dbf,DATA")
    ap.add_argument("--link", action="append", default=[],
                    help="связь вручную, можно несколько раз: potreb.cod_gor=danrasch.cod_gorod; "
                         "*.cod_gor=danrasch.cod_gorod значит во всех таблицах с полем cod_gor")
    ap.add_argument("--dbc", help="словарь базы VFP (.dbc): из него берутся ключи таблиц")
    ap.add_argument("--report-dir", default=".", help="куда положить report.md и report.json")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")

    models = read_models(args.models) if args.models else None
    tables = dbf_tables(args.src, args.encoding, models, args.exclude.split(","))
    if not tables:
        log.error("в %s нет файлов .dbf", args.src)
        return 2
    if args.command in ("analyze", "all"):
        write_report(analyze(tables, read_dbc_keys(args.dbc) if args.dbc else None, args.link), args.report_dir)
        if args.command == "analyze":
            return 0
    if not args.dsn:
        ap.error("для load и verify нужен --dsn")
    import psycopg
    with psycopg.connect(args.dsn, autocommit=True) as conn:
        p, order = plan(conn, tables)
        if args.command in ("load", "all"):
            load(conn, p, order)
        return 0 if verify(conn, p, order) else 1


if __name__ == "__main__":
    sys.exit(main())
