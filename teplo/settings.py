"""Настройки веб-приложения teplo-web.

Значения, зависящие от окружения, берутся из переменных окружения
(см. файл .env.example и README.md).
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Файл .env рядом с manage.py: строки ИМЯ=значение. Переменные окружения важнее.
_dotenv = BASE_DIR / ".env"
if _dotenv.exists():
    for _line in _dotenv.read_text(encoding="utf-8-sig").splitlines():
        _name, _sep, _value = _line.partition("=")
        if _sep and not _line.lstrip().startswith("#"):
            os.environ.setdefault(_name.strip(), _value.strip().strip('"'))


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
                "abonents.context_processors.raschet_mes",
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

# Папка, куда при переходе на новый месяц кладётся файл Abpt<ГГ><ММ>.dbf для 1С.
# Задаётся в «Справочниках» → «Настройки программы» (меняет Администратор); эта
# переменная — только запасной вариант, если там пусто.
TEPLO_1C_DIR = env("TEPLO_1C_DIR", "")

# Документы абонентам в PDF («Информация-счёт», акт): папка, где они хранятся по
# участкам и месяцам (в старой программе D:\Teplo_dog\Akt_potreb). Пусто — папка
# dokumenty рядом с программой.
TEPLO_DOC_DIR = env("TEPLO_DOC_DIR", "")
# Шрифт TrueType с кириллицей для PDF. Пусто — Arial из Windows (DejaVu Sans в Linux).
TEPLO_PDF_FONT = env("TEPLO_PDF_FONT", "")
TEPLO_PDF_FONT_BOLD = env("TEPLO_PDF_FONT_BOLD", "")

# Почта. Сервер, порт, адрес отправителя, тема и текст письма — в «Настройке рассылки
# писем» (smtp_nas, админка). Пароль почтового ящика лучше задать здесь, а не в smtp_nas.
TEPLO_SMTP_PASSWORD = env("TEPLO_SMTP_PASSWORD", "")
# Первый номер документа в реестре отправленных писем (продолжить нумерацию старой программы).
TEPLO_PISMO_NOMER = int(env("TEPLO_PISMO_NOMER", "1") or 1)

# Обмен с КРЭДО (РРИЦ) через COM-объект RRIC_COM_OBJECT (только Windows, pywin32).
# Сертификаты клиента — в хранилище «Личные» пользователя Windows, под которым работает
# программа; здесь — их отпечатки по участкам.
TEPLO_KREDO_ENDPOINT = env("TEPLO_KREDO_ENDPOINT", "http://www.rric.org:7742/RRIC_EP_SERVICE/WcfService")
TEPLO_KREDO_SERVICE_CERT = env("TEPLO_KREDO_SERVICE_CERT", "Rric Wcf Service")
TEPLO_KREDO_THUMB = {
    1: env("TEPLO_KREDO_THUMB_RYB", "eb89da47d567beee800118756e9b31568bf95072"),
    2: env("TEPLO_KREDO_THUMB_DUB", "e968ac9950fc5bd24953ec529980a8eac2e57e10"),
    3: env("TEPLO_KREDO_THUMB_KAM", "aedfd090498ab56b99b683782bba47fcd98d473c"),
}
