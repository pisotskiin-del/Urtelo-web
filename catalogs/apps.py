from django.apps import AppConfig


class CatalogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogs"
    verbose_name = "Справочники"

    def ready(self):
        from teplo.sqlite_unicode import register

        register()
