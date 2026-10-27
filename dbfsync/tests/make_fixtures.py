"""Создаёт тестовые таблицы DBF (формат VFP, кодировка cp866) для проверки dbfsync.

Данные выдуманы. Запуск: python dbfsync/tests/make_fixtures.py
"""

import datetime
from pathlib import Path

import dbf

OUT = Path(__file__).resolve().parent / "fixtures"

TABLES = {
    "org": (
        "kod N(5,0); naim C(60); inn C(12); kpp C(9); adres C(100); telefon C(30); "
        "data_dog D; aktiv L; prim M",
        [
            (1, 'ООО "Пример"', "7701000001", "770101001", "г. Город, ул. Первая, 1", "11-22-33",
             datetime.date(2019, 1, 15), True, "Демонстрационная запись"),
            (2, 'АО "Образец"', "7701000002", "770101001", "г. Город, ул. Вторая, 5", "44-55-66",
             datetime.date(2020, 3, 1), True, ""),
            (3, 'МУП "Тестовое"', "7701000003", "770101001", "г. Город, пр. Мира, 10", "",
             datetime.date(2021, 7, 20), False, "Договор расторгнут"),
        ],
    ),
    "objekt": (
        "kod N(6,0); kod_org N(5,0); naim C(60); adres C(100); plosh N(10,2); ob_em N(12,2)",
        [
            (10, 1, "Административное здание", "ул. Первая, 1", 1250.50, 4800.00),
            (11, 1, "Склад", "ул. Первая, 1, стр. 2", 600.00, 2400.00),
            (20, 2, "Офис", "ул. Вторая, 5", 830.25, 3100.00),
            (30, 0, "Котельная (абонент не указан)", "ул. Третья, 7", 95.00, 310.00),
        ],
    ),
    "tarif": (
        "kod N(3,0); naim C(40); cena N(12,4); data_s D",
        [
            (1, "Отопление, Гкал", 2150.3700, datetime.date(2026, 1, 1)),
            (2, "Горячая вода, м3", 198.4500, datetime.date(2026, 1, 1)),
        ],
    ),
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (spec, rows) in TABLES.items():
        for old in OUT.glob(f"{name}.*"):
            old.unlink()
        table = dbf.Table(str(OUT / f"{name}.dbf"), spec, dbf_type="vfp", codepage="cp866")
        table.open(dbf.READ_WRITE)
        for row in rows:
            table.append(row)
        table.close()
        print(f"{name}.dbf: {len(rows)} записей")


if __name__ == "__main__":
    main()
