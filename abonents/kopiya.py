"""Полная копия данных закрытого месяца.

При переходе на новый месяц все таблицы программы (справочники, абоненты,
приборы, тарифы, потери, теплосчётчики, лимиты, подписанты, реестр писем и
т. д. — приложения catalogs и abonents) копируются в отдельный файл SQLite
arhiv_mesyacev/ГГГГ-ММ.sqlite3 в том виде, в каком они были до перехода. Это то
же самое, что раньше делали вручную, копируя программу на другой компьютер.

При просмотре закрытого месяца (abonents.prosmotr) все чтения этих таблиц идут
из копии (ArhivRouter), поэтому карточки, итоги, отчеты и документы
показывают ровно то, что было до перехода. Копия открывается только для
чтения. Не копируются архивы месяцев (MesArhiv) и настройки программы
(Nastroika) — они всегда берутся из рабочей базы.
"""

import contextvars
import os
import threading
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db import connections

APPS = ("catalogs", "abonents")
NE_KOPIROVAT = {("abonents", "mesarhiv"), ("abonents", "nastroika")}
PACHKA = 500

_alias = contextvars.ContextVar("teplo_arhiv_alias", default=None)


def papka():
    return Path(getattr(settings, "TEPLO_ARHIV_DIR", "") or Path(settings.BASE_DIR) / "arhiv_mesyacev")


def put(mes, god):
    return papka() / f"{god}-{mes:02d}.sqlite3"


def est(mes, god):
    return put(mes, god).is_file()


def modeli():
    """Модели, данные которых входят в копию месяца."""
    out = []
    for label in APPS:
        for model in apps.get_app_config(label).get_models():
            if (model._meta.app_label, model._meta.model_name) in NE_KOPIROVAT:
                continue
            if not model._meta.managed or model._meta.proxy:
                continue
            out.append(model)
    return out


def _podklyuchit(alias, name, chtenie):
    """Подключение к файлу SQLite только в этом потоке. В connections.settings
    его не добавляем: сервер многопоточный, и менять общий словарь подключений на
    ходу нельзя."""
    from django.db.backends.sqlite3.base import DatabaseWrapper
    cfg = {"ENGINE": "django.db.backends.sqlite3", "NAME": name}
    if chtenie:
        cfg["NAME"] = f"file:{Path(name).as_posix()}?mode=ro"
        cfg["OPTIONS"] = {"uri": True}
    cfg = connections.configure_settings({"default": cfg})["default"]
    connections[alias] = DatabaseWrapper(cfg, alias)
    return connections[alias]


def _otklyuchit(alias):
    try:
        conn = getattr(connections._connections, alias)
    except AttributeError:
        return
    try:
        conn.close()
    finally:
        del connections[alias]


def sozdat(mes, god):
    """Скопировать текущие данные в файл месяца (mes, god). Пишет во временный
    файл и только потом заменяет им файл месяца. Возвращает путь."""
    final = put(mes, god)
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp = final.with_name(final.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    alias = "teplo_arhiv_novyj"
    conn = _podklyuchit(alias, str(tmp), chtenie=False)
    try:
        spisok = modeli()
        with conn.schema_editor() as se:
            for model in spisok:
                se.create_model(model)
        with conn.constraint_checks_disabled():
            for model in spisok:
                pachka = []
                for obj in model._base_manager.using("default").order_by().iterator(chunk_size=2000):
                    pachka.append(obj)
                    if len(pachka) >= PACHKA:
                        model._base_manager.using(alias).bulk_create(pachka)
                        pachka = []
                if pachka:
                    model._base_manager.using(alias).bulk_create(pachka)
    except BaseException:
        _otklyuchit(alias)
        if tmp.exists():
            tmp.unlink()
        raise
    _otklyuchit(alias)
    os.replace(tmp, final)
    return final


def udalit(mes, god):
    """Убрать копию месяца (при отмене перехода)."""
    _otklyuchit(alias_mesyaca(mes, god))
    p = put(mes, god)
    if p.exists():
        p.unlink()


def alias_mesyaca(mes, god):
    return f"teplo_arhiv_{god}_{mes:02d}"


_provereny = set()   # (путь, время изменения) копий, схема которых уже сверена
_zamok = threading.Lock()


def obnovit_shemu(path):
    """Добавить в копию месяца таблицы и колонки, появившиеся в программе после
    закрытия месяца (иначе новые версии программы не смогут её читать). Данные
    копии не меняются: в новых колонках пусто или значение по умолчанию."""
    key = (str(path), path.stat().st_mtime_ns)
    if key in _provereny:
        return
    with _zamok:
        if key in _provereny:
            return
        alias = "teplo_arhiv_shema"
        conn = _podklyuchit(alias, str(path), chtenie=False)
        try:
            with conn.cursor() as c:
                tablicy = set(conn.introspection.table_names(c))
            with conn.schema_editor() as se:
                for model in modeli():
                    t = model._meta.db_table
                    if t not in tablicy:
                        se.create_model(model)
                        continue
                    with conn.cursor() as c:
                        est_kol = {col.name for col in conn.introspection.get_table_description(c, t)}
                    for f in model._meta.local_concrete_fields:
                        if f.column not in est_kol:
                            se.add_field(model, f)
        finally:
            _otklyuchit(alias)
        _provereny.add((str(path), path.stat().st_mtime_ns))


def otkryt(mes, god):
    """Открыть копию месяца (только чтение) в этом потоке: имя подключения или
    None, если копии нет. Закрывает zakryt()."""
    if not est(mes, god):
        return None
    obnovit_shemu(put(mes, god))
    alias = alias_mesyaca(mes, god)
    _otklyuchit(alias)
    _podklyuchit(alias, str(put(mes, god)), chtenie=True)
    return alias


def zakryt(alias):
    _otklyuchit(alias)


class Vklyuchit:
    """with Vklyuchit(alias): чтения таблиц программы — из копии месяца."""

    def __init__(self, alias):
        self.alias = alias

    def __enter__(self):
        self.token = _alias.set(self.alias)
        return self

    def __exit__(self, *exc):
        _alias.reset(self.token)


def tekushchij():
    return _alias.get()


class ArhivRouter:
    """В просмотре закрытого месяца чтение и запись таблиц catalogs/abonents идут
    в копию месяца (она открыта только для чтения, поэтому любая запись там
    завершится ошибкой и рабочую базу не тронет). Сеансы, пользователи и права —
    всегда из рабочей базы."""

    def _db(self, model):
        alias = _alias.get()
        if alias and model._meta.app_label in APPS and \
                (model._meta.app_label, model._meta.model_name) not in NE_KOPIROVAT:
            return alias
        return None

    def db_for_read(self, model, **hints):
        return self._db(model)

    def db_for_write(self, model, **hints):
        return self._db(model)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, **hints):
        # В копии месяца таблицы создаёт sozdat(), миграции туда не идут.
        return False if db.startswith("teplo_arhiv_") else None
