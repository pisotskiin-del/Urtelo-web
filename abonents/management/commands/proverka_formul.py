"""Проверка формул расчёта на данных старой программы.

Читает potreb.dbf, danrasch.dbf и sp_teplpoteri.dbf старой программы сразу
после её расчёта, выполняет в памяти расчёт новой программы на тех же исходных
данных (база новой программы не меняется) и сравнивает каждое рассчитанное
поле у каждого лицевого. Расхождение здесь означает разницу в формулах, а не в
данных.
"""

import copy
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalogs.models import Danrasch, Potreb, SpTeplpoteri
from dbfsync.importer import _find_file, column_map, convert
from dbfsync.reader import open_dbf

from abonents import raschet
from abonents.layout import RASCHET

POROG = Decimal("0.001")


def zagruzit(model, papka):
    """Записи таблицы DBF как объекты модели в памяти, в порядке записей."""
    try:
        path = _find_file(Path(papka), model.dbf_source)
    except FileNotFoundError:
        raise CommandError(f"Нет файла {Path(papka) / model.dbf_source}") from None
    t = open_dbf(path, settings.DBF_ENCODING or None)
    cm = column_map(model)
    names = {f.name.upper() for f in t.fields}
    out = []
    for rec in t:
        up = {k.upper(): v for k, v in rec.items()}
        out.append(model(**{f.attname: convert(f, up.get(col), t.encoding) for f, col in cm.items() if col in names}))
    return out


def sravnit(papka):
    """(старые записи, новые записи, {поле: [(л/№, город, старое, новое)]}, города)."""
    recs = zagruzit(Potreb, papka)
    cities = {d.cod_gorod: d for d in zagruzit(Danrasch, papka) if d.cod_gorod is not None}
    sp_by_ln = {}
    for sp in zagruzit(SpTeplpoteri, papka):
        sp_by_ln.setdefault(sp.ln, sp)
    old = [copy.copy(r) for r in recs]
    _, pt, _ = raschet.compute(recs, cities, sp_by_ln)
    diff = defaultdict(list)
    for o, r in zip(old, recs):
        # Старая программа считает только статус 60, новая — 60 и 62.
        if o.d_stat != 60 and r.d_stat not in RASCHET:
            continue
        for f in sorted(pt.changed):
            a, b = Decimal(getattr(o, f) or 0), Decimal(getattr(r, f) or 0)
            if abs(a - b) > POROG:
                diff[f].append((r.potreb_id, r.cod_gor_id, a, b))
    return old, recs, diff, cities


class Command(BaseCommand):
    help = "Проверить формулы расчёта на данных старой программы (база не меняется)."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Папка dbf старой программы")

    def handle(self, *args, **opts):
        papka = opts["dir"] or ""
        if not Path(papka).is_dir():
            raise CommandError(f"Нет папки {papka}")
        old, recs, diff, cities = sravnit(papka)
        self.stdout.write(f"Лицевых в старой программе: {len(old)}")
        for code, c in sorted(cities.items()):
            a = sum(Decimal(o.nac_vsego or 0) for o in old if o.cod_gor_id == code and o.d_stat == 60)
            b = sum(Decimal(r.nac_vsego or 0) for r in recs if r.cod_gor_id == code and r.d_stat in RASCHET)
            self.stdout.write(f"{c.name_gorod} ({c.nom_mes}.{c.god}): предъявлено к оплате — старая {a}, "
                              f"новая по тем же данным {b}")
        if not diff:
            self.stdout.write(self.style.SUCCESS(
                "Формулы совпадают: расчёт новой программы на этих данных дал те же значения у всех лицевых. "
                "Если итоги программ отличаются, причина в исходных данных — см. sverka-rascheta.bat."))
            return
        for f, rows in diff.items():
            self.stdout.write(self.style.WARNING(f"{f}: расходится у {len(rows)} лицевых"))
            for pid, gor, a, b in rows[:20]:
                self.stdout.write(f"    Л/№ {pid} (участок {gor}): старая {a}, новая {b}")
