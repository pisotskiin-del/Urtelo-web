"""Загрузить архивы месяцев старой программы (Arhiv\\PoMMГГГГ.dbf,
DaMMГГГГ.dbf, taMMГГГГ.dbf) в архив месяцев новой программы, чтобы отчеты
за период видели и месяцы до ее запуска.

Месяцы, которые уже есть в архиве, пропускаются (закрытые в новой
программе — всегда; загруженные раньше — если не указан --zamenit).
"""

import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from abonents.models import MesArhiv
from catalogs.models import Danrasch, Potreb, Tarif
from dbfsync.importer import column_map, convert
from dbfsync.reader import open_dbf

FILE = re.compile(r"^(po|da|ta)(\d\d)(\d{4})\.dbf$", re.I)


def read_rows(model, path):
    table = open_dbf(path, settings.DBF_ENCODING or None)
    cols = column_map(model)
    names = {f.name.upper() for f in table.fields}
    out = []
    for rec in table:
        out.append({f.attname: convert(f, rec.get(col), table.encoding)
                    for f, col in cols.items() if col in names})
    return out


class Command(BaseCommand):
    help = "Загрузить архивы месяцев старой программы (Arhiv\\Po/Da/taMMГГГГ.dbf) для отчетов за период."

    def add_arguments(self, parser):
        default = Path(settings.DBF_SOURCE_DIR).parent / "Arhiv" if settings.DBF_SOURCE_DIR else ""
        parser.add_argument("--dir", default=str(default), help="Каталог Arhiv старой программы")
        parser.add_argument("--zamenit", action="store_true",
                            help="Загрузить заново месяцы, уже загруженные из старой программы")

    def handle(self, *args, **opts):
        folder = Path(opts["dir"])
        if not folder.is_dir():
            raise CommandError(f"Нет каталога {folder}")
        files = {}
        for p in folder.iterdir():
            m = FILE.match(p.name)
            if m:
                files.setdefault((int(m.group(2)), int(m.group(3))), {})[m.group(1).lower()] = p
        added = skipped = 0
        for (mes, god), parts in sorted(files.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            if "po" not in parts or not 1 <= mes <= 12:
                continue
            existing = MesArhiv.objects.filter(nom_mes=mes, god=god)
            if existing.filter(istochnik=MesArhiv.WEB).exists() or \
                    (existing.exists() and not opts["zamenit"]):
                skipped += 1
                continue
            potreb = read_rows(Potreb, parts["po"])
            tables = {"potreb": potreb,
                      "danrasch": read_rows(Danrasch, parts["da"]) if "da" in parts else [],
                      "tarif": read_rows(Tarif, parts["ta"]) if "ta" in parts else []}
            with transaction.atomic():
                existing.filter(istochnik=MesArhiv.DBF).delete()
                arh = MesArhiv(nom_mes=mes, god=god, user="arhiv_import", istochnik=MesArhiv.DBF,
                               potreb_count=len(potreb),
                               nac_vsego=sum((r.get("nac_vsego") or Decimal(0) for r in potreb), Decimal(0)))
                arh.set_tables(tables)
                arh.save()
            added += 1
            self.stdout.write(f"{mes:02d}.{god}: {len(potreb)} записей"
                              + ("" if "da" in parts else " (нет Da — без исходных данных расчета)"))
        self.stdout.write(self.style.SUCCESS(f"Загружено месяцев: {added}, пропущено (уже есть): {skipped}"))
