"""Перенести все данные программы из SQLite (db.sqlite3) в PostgreSQL.

Запускается уже настроенной на PostgreSQL программой (DB_ENGINE=postgresql в
.env), в пустую базу:

    python manage.py perenos_v_postgres --iz D:\\teplo-web\\db.sqlite3

Шаги: создаются таблицы (migrate), из SQLite выгружаются все данные
(dumpdata: абоненты, справочники, архивы месяцев, реестр писем, пользователи
и роли), строки длиннее поля обрезаются (SQLite длину не проверяет,
PostgreSQL — проверяет), данные загружаются (loaddata), затем число записей
каждой таблицы сверяется с исходной базой.
"""

import json
import tempfile
from pathlib import Path

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, models

ISKLYUCHIT = ["contenttypes", "auth.permission", "sessions", "admin.logentry"]


def obrezat(fail, stdout):
    """Обрезать в выгрузке строки длиннее max_length поля. Возвращает число правок."""
    data = json.loads(Path(fail).read_text(encoding="utf-8"))
    dliny = {}
    pravki = 0
    for obj in data:
        model = obj["model"]
        if model not in dliny:
            m = apps.get_model(model)
            dliny[model] = {f.name: f.max_length for f in m._meta.concrete_fields
                            if isinstance(f, models.CharField) and f.max_length}
        for pole, n in dliny[model].items():
            v = obj["fields"].get(pole)
            if isinstance(v, str) and len(v) > n:
                stdout.write(f"  обрезано {model}.{pole} (запись {obj.get('pk')}): «{v}» → «{v[:n]}»")
                obj["fields"][pole] = v[:n]
                pravki += 1
    Path(fail).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return pravki


class Command(BaseCommand):
    help = "Перенести все данные из SQLite (db.sqlite3) в PostgreSQL."

    def add_arguments(self, parser):
        parser.add_argument("--iz", required=True, help="Файл базы SQLite, например D:\\teplo-web\\db.sqlite3")

    def handle(self, *args, **opts):
        iz = Path(opts["iz"])
        if not iz.is_file():
            raise CommandError(f"Нет файла {iz}")
        if connections["default"].vendor != "postgresql":
            raise CommandError("Программа настроена не на PostgreSQL: задайте DB_ENGINE=postgresql и DB_* в .env")
        connections.databases["istochnik"] = {**connections.databases["default"],
                                              "ENGINE": "django.db.backends.sqlite3", "NAME": str(iz)}
        modeli = [m for m in apps.get_models() if m._meta.managed and not m._meta.proxy]
        from catalogs.models import Potreb
        if Potreb._meta.db_table in connections["default"].introspection.table_names() and \
                Potreb.objects.using("default").exists():
            raise CommandError("В базе PostgreSQL уже есть абоненты: перенос делается в новую пустую базу")
        call_command("migrate", verbosity=0)
        # Миграции заполняют часть таблиц начальными значениями — их заменят данные из SQLite.
        call_command("flush", interactive=False, verbosity=0)
        self.stdout.write("Выгрузка из SQLite…")
        with tempfile.TemporaryDirectory() as tmp:
            fail = Path(tmp) / "dannye.json"
            # Файл открываем сами в UTF-8: Django 4.2 (старый Python) пишет --output
            # в кодировке Windows (cp1251).
            with open(fail, "w", encoding="utf-8") as f:
                call_command("dumpdata", database="istochnik", natural_foreign=True, natural_primary=True,
                             exclude=ISKLYUCHIT, stdout=f, verbosity=0)
            pravki = obrezat(fail, self.stdout)
            self.stdout.write("Загрузка в PostgreSQL…")
            call_command("loaddata", str(fail), database="default", verbosity=0)
        self.stdout.write("Сверка числа записей…")
        oshibki = []
        for m in modeli:
            if m._meta.label_lower in ("auth.permission", "contenttypes.contenttype", "sessions.session",
                                       "admin.logentry"):
                continue
            try:
                a = m.objects.using("istochnik").count()
            except Exception:
                continue   # таблицы нет в старой базе (например, тестовые модели)
            b = m.objects.using("default").count()
            if a != b:
                oshibki.append(f"{m._meta.label}: в SQLite {a}, в PostgreSQL {b}")
        if oshibki:
            raise CommandError("Число записей не совпало:\n" + "\n".join(oshibki))
        self.stdout.write(self.style.SUCCESS(
            f"Готово: перенесены все таблицы, число записей совпадает; обрезано длинных строк: {pravki}"))
