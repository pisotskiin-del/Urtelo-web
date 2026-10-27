from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dbfsync.schema import apply_relations, inspect_directory, load_labels, load_relations, render_models

DEFAULT_LABELS = Path(__file__).resolve().parents[2] / "labels" / "ur_teplo.json"
DEFAULT_RELATIONS = Path(__file__).resolve().parents[2] / "labels" / "ur_teplo_relations.json"


class Command(BaseCommand):
    help = "Построить модели Django (catalogs/models.py) по заголовкам таблиц DBF."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Каталог с таблицами .dbf")
        parser.add_argument("--encoding", default=settings.DBF_ENCODING, help="cp866, cp1251… (по умолчанию из заголовка)")
        parser.add_argument("--labels", default="", help="labels.json с русскими названиями таблиц и полей")
        parser.add_argument("--relations", default=str(DEFAULT_RELATIONS),
                            help="JSON с ключами и связями между таблицами (пусто — без связей)")
        parser.add_argument("--output", default="", help="Куда записать код (по умолчанию в stdout)")

    def handle(self, *args, **opts):
        directory = Path(opts["dir"])
        if not directory.is_dir():
            raise CommandError(f"Каталог не найден: {directory}")
        labels_path = opts["labels"] or (
            directory / "labels.json" if (directory / "labels.json").exists() else DEFAULT_LABELS
        )
        tables = inspect_directory(directory, encoding=opts["encoding"], labels=load_labels(labels_path))
        if not tables:
            raise CommandError(f"В каталоге {directory} нет файлов .dbf")
        for missing in apply_relations(tables, load_relations(opts["relations"])):
            self.stderr.write(self.style.WARNING(f"Связь пропущена, нет таблицы или поля: {missing}"))
        code = render_models(tables, source_dir=directory.name)
        if opts["output"]:
            Path(opts["output"]).write_text(code, encoding="utf-8")
            self.stderr.write(f"Записано {len(tables)} моделей в {opts['output']}")
        else:
            self.stdout.write(code)
        for t in tables:
            self.stderr.write(f"  {t.file_name:<20} → {t.class_name:<20} полей: {len(t.fields):>3}, записей: {t.record_count}")
