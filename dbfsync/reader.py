"""Чтение таблиц DBF (Visual FoxPro) через dbfread с поправками для VFP."""

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dbfread import DBF, FieldParser

# Сколько записей просматривать, чтобы угадать кодировку.
ENCODING_SAMPLE = 500


class VfpFieldParser(FieldParser):
    """Парсер, который понимает типы VFP, отсутствующие в dbfread,
    не падает на «грязных» значениях (возвращает None) и считает их
    по полям в table.parse_errors."""

    def parseN(self, field, data):
        # Дробные числа сразу в Decimal, без промежуточного float.
        if not field.decimal_count:
            return super().parseN(field, data)
        text = data.strip().strip(b"*").replace(b",", b".")
        if not text:
            return None
        return Decimal(text.decode("ascii"))

    def parseV(self, field, data):
        # Varchar: VFP дополняет значение нулями/пробелами до длины поля.
        return self.decode_text(data.rstrip(b"\0 "))

    def parseQ(self, field, data):
        return bytes(data)

    def parseW(self, field, data):
        return self.get_memo(self._parse_memo_index(data))

    def parse(self, field, data):
        try:
            return super().parse(field, data)
        except (ValueError, UnicodeDecodeError, InvalidOperation, OverflowError):
            errors = getattr(self.table, "parse_errors", None)
            if errors is not None:
                errors[field.name] += 1
            return None


def find_dbf_files(directory):
    """Все .dbf в каталоге и подкаталогах (без учёта регистра расширения)."""
    directory = Path(directory)
    return sorted(
        (p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() == ".dbf"),
        key=lambda p: str(p.relative_to(directory)).lower(),
    )


def _cyrillic_score(sample, encoding):
    text = sample.decode(encoding, errors="replace")
    letters = sum(1 for ch in text if "Ѐ" <= ch <= "ӿ")
    junk = sum(1 for ch in text if ord(ch) >= 0x80 and not ("Ѐ" <= ch <= "ӿ"))
    return letters - 2 * junk


def guess_encoding(path):
    """Для таблиц без кодировки в заголовке (language driver = 0) выбирает
    между cp866 и cp1251 по тому, в какой из них текстовые поля дают
    больше кириллицы и меньше мусора."""
    table = DBF(str(path), raw=True, ignore_missing_memofile=True)
    text_fields = [f.name for f in table.fields if f.type in ("C", "V")]
    chunks = []
    for i, record in enumerate(table):
        if i >= ENCODING_SAMPLE:
            break
        chunks += [record[name] for name in text_fields if record[name]]
    sample = b" ".join(c for c in chunks if any(b >= 0x80 for b in c))
    if not sample:
        return "cp1251"
    return max(("cp866", "cp1251"), key=lambda enc: _cyrillic_score(sample, enc))


def detect_encoding(path):
    table = DBF(str(path), raw=True, ignore_missing_memofile=True)
    if table.header.language_driver == 0 or table.encoding == "ascii":
        return guess_encoding(path)
    return table.encoding


def open_dbf(path, encoding=None, load_records=False):
    """Открыть таблицу. Если кодировка не задана, она берётся из заголовка
    (байт language driver), а если там пусто — угадывается по данным."""
    table = DBF(
        str(path),
        encoding=encoding or detect_encoding(path),
        parserclass=VfpFieldParser,
        ignore_missing_memofile=True,
        char_decode_errors="replace",
        load=load_records,
    )
    table.parse_errors = Counter()
    return table
