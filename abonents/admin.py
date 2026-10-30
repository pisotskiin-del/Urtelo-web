from django.contrib import admin

from .models import Podpisant, TarifGorod


@admin.register(Podpisant)
class PodpisantAdmin(admin.ModelAdmin):
    list_display = ["rol", "gorod", "doljnost", "fio"]


@admin.register(TarifGorod)
class TarifGorodAdmin(admin.ModelAdmin):
    list_display = ["gorod", "id_tar", "name_tar", "zn_tar", "diz_tar"]
    list_filter = ["gorod"]
