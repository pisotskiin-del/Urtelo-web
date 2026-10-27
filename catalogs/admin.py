from django.contrib import admin

from django.apps import apps

from .registry import SECRET_FIELDS, list_fields, search_fields

admin.site.site_header = "Теплоснабжение: администрирование"
admin.site.site_title = "Администрирование"
admin.site.index_title = "Справочники и пользователи"

# В админке все таблицы базы, а не только справочники из меню.
for _model in apps.get_app_config("catalogs").get_models():
    admin.site.register(
        _model,
        list_display=["__str__"] + [f.name for f in list_fields(_model)][1:],
        search_fields=[f.name for f in search_fields(_model)],
        exclude=[f.name for f in _model._meta.fields if f.name in SECRET_FIELDS],
        list_per_page=50,
    )
