from django.contrib import admin

from .models import KredoPriem, Pismo, Podpisant, TarifGorod


@admin.register(Podpisant)
class PodpisantAdmin(admin.ModelAdmin):
    list_display = ["rol", "gorod", "doljnost", "fio"]


@admin.register(TarifGorod)
class TarifGorodAdmin(admin.ModelAdmin):
    list_display = ["gorod", "id_tar", "name_tar", "zn_tar", "diz_tar"]
    list_filter = ["gorod"]


@admin.register(Pismo)
class PismoAdmin(admin.ModelAdmin):
    list_display = ["nomer", "created", "nom_mes", "god", "nom_dog", "potreb_id", "name_potre", "email", "vid", "status"]
    list_filter = ["status", "vid", "god", "cod_gor"]
    search_fields = ["name_potre", "email"]

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(KredoPriem)
class KredoPriemAdmin(admin.ModelAdmin):
    list_display = ["created", "user", "cod_gor", "nom_mes", "god", "istochnik", "strok", "razneseno", "razn_user"]
    list_filter = ["cod_gor", "god"]

    def has_change_permission(self, request, obj=None):
        return False
