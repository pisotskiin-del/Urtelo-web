"""Запись таблицы DBF в формате Visual FoxPro (как файлы старой программы).

Нужна для выгрузки в 1С: файл Abpt<ГГ><ММ>.dbf с той же структурой, что
dbf\\abot.dbf. Поддержаны типы C, N, D — других в выгрузке нет."""

import datetime
import struct
from decimal import ROUND_HALF_UP, Decimal

# Структура abot.dbf (снята с D:\teplo_dog\dbf\abot.dbf).
ABOT_FIELDS = [
    ("KOD", "N", 15, 0), ("KODABON", "N", 15, 0), ("NAME", "C", 150, 0), ("AKCEPT", "N", 1, 0),
    ("TARIF", "N", 20, 2), ("RAS_KOL", "N", 20, 2), ("ZAV_KOL", "N", 20, 2), ("RAS_SUM", "N", 18, 2),
    ("ZAV_SUM", "N", 18, 2), ("OP_KOL", "N", 20, 2), ("OP_SUM", "N", 20, 2), ("KODUSLUG", "N", 3, 0),
    ("NAMEUSLUG", "C", 100, 0), ("TARIFUE", "N", 20, 2), ("CITY", "N", 1, 0), ("RAS_CHET", "N", 16, 0),
    ("FISK_COD", "C", 11, 0), ("PERC_PENI", "N", 3, 0), ("KODUSLUG1", "N", 3, 0), ("NAME_CITY", "C", 15, 0),
    ("NAME_KATEG", "C", 50, 0), ("N_DOG", "C", 10, 0), ("DAT_DOG", "D", 8, 0),
]


def _cell(value, ftype, length, dec, encoding):
    if ftype == "C":
        raw = ("" if value is None else str(value)).encode(encoding, "replace")[:length]
        return raw.ljust(length, b" ")
    if ftype == "D":
        return value.strftime("%Y%m%d").encode() if isinstance(value, datetime.date) else b" " * 8
    if value is None:
        return b" " * length
    number = Decimal(value).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP)
    text = f"{number:.{dec}f}".encode()
    if len(text) > length:
        text = b"*" * length  # как FoxPro при переполнении
    return text.rjust(length, b" ")


def write(path_or_file, fields, rows, encoding="cp1251", codepage_mark=0xC9):
    """Записать rows (словари с ключами — именами полей) в DBF."""
    record_len = 1 + sum(f[2] for f in fields)
    header_len = 32 + 32 * len(fields) + 1 + 263  # 263 байта — ссылка на базу данных (VFP)
    today = datetime.date.today()
    out = bytearray()
    out += struct.pack("<BBBBIHH", 0x30, today.year - 1900, today.month, today.day, len(rows), header_len, record_len)
    out += bytes(16) + bytes([0, codepage_mark, 0, 0])
    offset = 1
    for name, ftype, length, dec in fields:
        out += name.encode("ascii").ljust(11, b"\0") + ftype.encode() + struct.pack("<I", offset)
        out += bytes([length, dec, 0]) + bytes(13)
        offset += length
    out += b"\r" + bytes(263)
    for row in rows:
        out += b" " + b"".join(_cell(row.get(name), t, l, d, encoding) for name, t, l, d in fields)
    out += b"\x1a"
    if hasattr(path_or_file, "write"):
        path_or_file.write(bytes(out))
    else:
        with open(path_or_file, "wb") as f:
            f.write(bytes(out))
