from django.apps import AppConfig


class TestappConfig(AppConfig):
    """Модели только для тестов dbfsync (подключаются при manage.py test)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dbfsync.testapp"
    label = "dbfsync_testapp"
