from django.contrib import admin

from .models import Podpisant


@admin.register(Podpisant)
class PodpisantAdmin(admin.ModelAdmin):
    list_display = ["rol", "gorod", "doljnost", "fio"]
