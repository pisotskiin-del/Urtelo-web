"""Список справочников, которые показываются в веб-интерфейсе.

Порядок и состав повторяют меню «Справочники» программы Urteplo
(MENUS\\gl_menu.mpr). Остальные таблицы базы доступны администратору
в админке (/admin/)."""

from django.apps import apps
from django.db import models
from django.http import Http404

# Имена моделей в порядке пунктов меню. Пусто — все модели по алфавиту.
CATALOG_ORDER = [
    "danrasch",           # Города (форма gorod)
    "minist",             # Министерства
    "gvskot",             # Котельные (форма koteln)
    "spbank",             # Банки (форма sp_bank)
    "kategorpot",         # Категории потребителя
    "tarif",              # Тарифы
    "udnorm",             # Удельные нормы (форма udnorma)
    "teplpot",            # Тепловые потери (форма poteri)
    "akcept",             # Акцепт
    # «Улицы» (sul) в меню есть, но не используются и не переносятся (27.10.2026).
    # «Настройка рассылки писем» (smtp_nas) хранит пароль почты, поэтому
    # она не в общем списке, а только в админке, и пароль там скрыт.
    "seturdevicelist",    # Справочник приборов учёта
    "seturdevtypelist",   # Типы приборов учёта
    "seturdevplacelist",  # Места установки приборов учёта
    "seturdevice",        # Информация о приборах учёта
    "seturplomblist",     # Справочник пломб
]

# Поля, которые не показываются ни в справочниках, ни в админке.
SECRET_FIELDS = {"password"}

LIST_COLUMNS_LIMIT = 8
SEARCH_TYPES = (models.CharField, models.TextField)


def catalog_models():
    found = {m._meta.model_name: m for m in apps.get_app_config("catalogs").get_models()}
    if CATALOG_ORDER:
        return [found[name] for name in CATALOG_ORDER if name in found]
    return sorted(found.values(), key=lambda m: str(m._meta.verbose_name_plural))


def get_model(slug):
    for model in catalog_models():
        if model._meta.model_name == slug:
            return model
    raise Http404("Справочник не найден")


def data_fields(model):
    return [
        f for f in model._meta.concrete_fields
        if not f.primary_key and not isinstance(f, models.BinaryField) and f.name not in SECRET_FIELDS
    ]


def list_fields(model):
    return [f for f in data_fields(model) if not isinstance(f, models.TextField)][:LIST_COLUMNS_LIMIT]


def search_fields(model):
    return [f for f in data_fields(model) if isinstance(f, SEARCH_TYPES)]
