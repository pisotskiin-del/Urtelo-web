from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dbfsync.importer import DuplicateKeyError, dbf_models, import_table, load_fixes, truncate_tables

DEFAULT_FIXES = Path(__file__).resolve().parents[2] / "labels" / "ur_teplo_fixes.json"


class Command(BaseCommand):
    help = "Загрузить данные из таблиц DBF в базу приложения и сверить число записей."

    def add_arguments(self, parser):
        parser.add_argument("--dir", default=settings.DBF_SOURCE_DIR, help="Каталог с таблицами .dbf")
        parser.add_argument("--encoding", default=settings.DBF_ENCODING)
        parser.add_argument("--only", nargs="*", default=[], help="Имена моделей, например Org Tarif")
        parser.add_argument("--append", action="store_true", help="Не очищать таблицы перед загрузкой")
        parser.add_argument("--app", default="catalogs", help="Приложение с моделями (для тестов)")
        parser.add_argument("--fixes", default="", help="JSON с исправлениями данных (для catalogs по умолчанию ur_teplo_fixes.json)")

    def handle(self, *args, **opts):
        targets = dbf_models(opts["app"])
        if opts["only"]:
            wanted = {n.lower() for n in opts["only"]}
            targets = [m for m in targets if m.__name__.lower() in wanted]
        if not targets:
            raise CommandError("Нет моделей для загрузки. Сначала выполните dbf_inspect и migrate.")

        with transaction.atomic():  # ссылки проверяются в конце, когда загружены все таблицы
            failed = self.load(targets, opts)
            if failed:
                transaction.set_rollback(True)  # при ошибке база остаётся как была
        if failed:
            raise CommandError("Загрузка завершилась с ошибками, см. выше. Данные в базе не изменены.")

    def load(self, targets, opts):
        if not opts["append"]:
            truncate_tables(targets)
        failed = False
        fixes_path = opts["fixes"] or (DEFAULT_FIXES if opts["app"] == "catalogs" else "")
        fixes = load_fixes(fixes_path) if fixes_path else {}
        for model in targets:
            try:
                source, loaded, bad, fixed = import_table(model, opts["dir"], opts["encoding"], truncate=False, fixes=fixes)
            except DuplicateKeyError as exc:
                failed = True
                self.stderr.write(self.style.ERROR(str(exc)))
                continue
            except FileNotFoundError as exc:
                failed = True
                self.stderr.write(self.style.ERROR(f"{model.__name__}: {exc}"))
                continue
            ok = opts["append"] or source == loaded
            failed |= not ok
            style = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(style(f"{model.dbf_source:<20} DBF: {source:>7}  БД: {loaded:>7}  {'OK' if ok else 'РАСХОЖДЕНИЕ'}"))
            for column, count in sorted(bad.items()):
                self.stdout.write(self.style.WARNING(f"    {column}: нечитаемых значений {count}, записаны пустыми"))
            for column, count in sorted(fixed.items()):
                if count:
                    self.stdout.write(f"    {column}: исправлено значений {count} (см. {Path(fixes_path).name})")
        return failed
