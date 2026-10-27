"""Поиск без учёта регистра для русских букв.

В SQLite функции LOWER и оператор LIKE не различают регистр только для латиницы,
поэтому поиск «образец» не находил «Образец». Для SQLite регистрируем свою функцию
UNICODE_LOWER и ищем по ней; встроенный LIKE не трогаем (SQLite сам пользуется им
при изменении схемы). В PostgreSQL обычный LOWER работает с любыми буквами."""

from django.db.backends.signals import connection_created
from django.db.models import CharField, Func


def _unicode_lower(value):
    return None if value is None else str(value).lower()


def _install(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_function("UNICODE_LOWER", 1, _unicode_lower, deterministic=True)


def register():
    connection_created.connect(_install, dispatch_uid="teplo_sqlite_unicode_lower")


class UnicodeLower(Func):
    """LOWER, который понимает кириллицу и в SQLite."""

    function = "LOWER"
    output_field = CharField()

    def as_sqlite(self, compiler, connection, **extra_context):
        return super().as_sql(compiler, connection, function="UNICODE_LOWER", **extra_context)
