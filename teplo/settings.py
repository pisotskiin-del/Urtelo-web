"""Настройки веб-приложения teplo-web.

Значения, зависящие от окружения, берутся из переменных окружения
(см. файл .env.example и README.md).
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "catalogs",
    "abonents",
    "dbfsync",
]

# Тестовые модели dbfsync нужны только при запуске тестов.
if len(sys.argv) > 1 and sys.argv[1] == "test":
    INSTALLED_APPS.append("dbfsync.testapp")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "teplo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.roles",
            ],
        },
    },
]

WSGI_APPLICATION = "teplo.wsgi.application"

# По умолчанию SQLite, чтобы приложение запускалось без настройки.
# Для PostgreSQL задайте DB_ENGINE=postgresql и параметры DB_* (см. README).
if env("DB_ENGINE", "sqlite") == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "teplo"),
            "USER": env("DB_USER", "teplo"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "abonents:index"
LOGOUT_REDIRECT_URL = "login"

# Каталог с таблицами DBF старой программы и их кодировка по умолчанию.
# Пустая кодировка означает «определить по заголовку DBF».
DBF_SOURCE_DIR = env("DBF_SOURCE_DIR", r"D:\teplo_dog\dbf")
DBF_ENCODING = env("DBF_ENCODING", "")

CATALOG_PAGE_SIZE = 50

# Папка, куда при переходе на новый месяц кладётся файл Abot<ГГ><ММ>.dbf для 1С
# (в старой программе \\SERVER-B\Abon_teplo1C). Пусто — файл только скачивается
# со страницы «Новый месяц».
TEPLO_1C_DIR = os.environ.get("TEPLO_1C_DIR", "")
