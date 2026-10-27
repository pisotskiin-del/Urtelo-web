"""Чтение контейнера базы данных VFP (.dbc).

В заголовке DBF имя поля обрезано до 10 символов, а полное имя хранится
в .dbc. Отсюда берём полные имена полей таблиц, входящих в базу."""

import shutil
import tempfile
from pathlib import Path

from dbfread import DBF


def find_dbc_files(directory):
    return sorted(p for p in Path(directory).rglob("*") if p.is_file() and p.suffix.lower() == ".dbc")


def read_long_field_names(dbc_path):
    """{имя таблицы в нижнем регистре: [полные имена полей по порядку]}."""
    dbc_path = Path(dbc_path)
    with tempfile.TemporaryDirectory() as tmp:
        # dbfread ищет memo рядом с таблицей под расширением .fpt, а у .dbc это .dct.
        shutil.copy(dbc_path, Path(tmp) / "catalog.dbf")
        dct = next((p for p in dbc_path.parent.iterdir()
                    if p.stem.lower() == dbc_path.stem.lower() and p.suffix.lower() == ".dct"), None)
        if dct:
            shutil.copy(dct, Path(tmp) / "catalog.fpt")
        catalog = DBF(str(Path(tmp) / "catalog.dbf"), encoding="cp866",
                      ignore_missing_memofile=True, char_decode_errors="replace", load=True)
    names = {r["OBJECTID"]: r["OBJECTNAME"].strip() for r in catalog}
    tables = {}
    for r in catalog:
        if r["OBJECTTYPE"].strip() == "Field":
            table = names.get(r["PARENTID"], "").lower()
            tables.setdefault(table, []).append(r["OBJECTNAME"].strip())
    return tables


def long_names_for(directory):
    """Полные имена полей из всех .dbc каталога (первый найденный выигрывает)."""
    result = {}
    for dbc in find_dbc_files(directory):
        for table, fields in read_long_field_names(dbc).items():
            result.setdefault(table, fields)
    return result
