"""Перенести показания приборов из potreb.dbf старой программы в новую.

Меняются только поля показаний (по умолчанию pok_new, pok_old — отопление,
pok_newg, pok_oldg — ГВС) у лицевых, которые есть в обеих программах;
остальное, что уже правили в новой программе (коды КРЭДО, карточки),
не трогается. Без --zapisat команда только показывает, что изменится.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogs.models import Potreb
from dbfsync.importer import column_map, convert
from dbfsync.reader import open_dbf

POLYA = ["pok_new", "pok_old", "pok_newg", "pok_oldg"]


class Command(BaseCommand):
    help = "Перенести показания приборов из potreb.dbf старой программы (без --zapisat — только показать)."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Папка dbf старой программы")
        parser.add_argument("--polya", nargs="*", default=POLYA, help=f"Поля (по умолчанию {' '.join(POLYA)})")
        parser.add_argument("--zapisat", action="store_true", help="Записать изменения")

    def handle(self, *args, **opts):
        path = Path(opts["dir"] or "") / "potreb.dbf"
        if not path.is_file():
            raise CommandError(f"Нет файла {path}")
        cols = {f.attname: (f, col) for f, col in column_map(Potreb).items()}
        polya = [p.lower() for p in opts["polya"]]
        neizv = [p for p in polya if p not in cols]
        if neizv:
            raise CommandError(f"Неизвестные поля: {', '.join(neizv)}")
        table = open_dbf(path, settings.DBF_ENCODING or None)
        names = {f.name.upper() for f in table.fields}
        polya = [p for p in polya if cols[p][1] in names]
        id_col = cols["potreb_id"][1]
        staroe = {}
        for rec in table:
            pid = rec.get(id_col)
            if pid is not None:
                staroe[int(pid)] = {p: convert(cols[p][0], rec.get(cols[p][1]), table.encoding) for p in polya}
        izm, net = [], 0
        for p in Potreb.objects.only("potreb_id", "name_potre", *polya).order_by("potreb_id"):
            s = staroe.get(p.potreb_id)
            if s is None:
                net += 1
                continue
            raz = {k: v for k, v in s.items() if v != getattr(p, k)}
            if raz:
                izm.append((p, raz))
        for p, raz in izm[:30]:
            self.stdout.write(f"Л/№ {p.potreb_id} {(p.name_potre or '').strip()[:40]}: " + ", ".join(
                f"{k} {getattr(p, k)} → {v}" for k, v in raz.items()))
        if len(izm) > 30:
            self.stdout.write(f"… и ещё {len(izm) - 30}")
        self.stdout.write(f"Лицевых с другими показаниями: {len(izm)}; нет в старой программе: {net}")
        if not opts["zapisat"]:
            self.stdout.write("Ничего не записано. Чтобы перенести, запустите ещё раз с --zapisat.")
            return
        with transaction.atomic():
            for p, raz in izm:
                Potreb.objects.filter(pk=p.pk).update(**raz)
        self.stdout.write(self.style.SUCCESS(f"Перенесены показания {len(izm)} лицевых"))
