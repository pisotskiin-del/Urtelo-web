"""Тестовые модели по таблицам из dbfsync/tests/fixtures, включая связь."""

from django.db import models

from catalogs.models import DbfModel


class Objekt(DbfModel):
    dbf_source = "objekt.dbf"

    kod = models.IntegerField("Код", null=True, blank=True)
    kod_org = models.ForeignKey(
        "Org", models.PROTECT, verbose_name="Организация", to_field="kod",
        db_column="kod_org", null=True, blank=True,
    )
    naim = models.CharField("Наименование", max_length=60, null=True, blank=True)
    adres = models.CharField("Адрес", max_length=100, null=True, blank=True)
    plosh = models.DecimalField("Площадь, м2", max_digits=10, decimal_places=2, null=True, blank=True)
    ob_em = models.DecimalField("Объём, м3", max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "test_objekt"


class Org(DbfModel):
    dbf_source = "org.dbf"

    kod = models.IntegerField("Код", unique=True, null=True, blank=True)
    naim = models.CharField("Наименование", max_length=60, null=True, blank=True)
    inn = models.CharField("ИНН", max_length=12, null=True, blank=True)
    kpp = models.CharField("КПП", max_length=9, null=True, blank=True)
    adres = models.CharField("Адрес", max_length=100, null=True, blank=True)
    telefon = models.CharField("Телефон", max_length=30, null=True, blank=True)
    data_dog = models.DateField("Дата договора", null=True, blank=True)
    aktiv = models.BooleanField("Действует", null=True)
    prim = models.TextField("Примечание", null=True, blank=True)

    class Meta:
        db_table = "test_org"


class Tarif(DbfModel):
    dbf_source = "tarif.dbf"

    kod = models.IntegerField("Код", null=True, blank=True)
    naim = models.CharField("Наименование", max_length=40, null=True, blank=True)
    cena = models.DecimalField("Цена", max_digits=12, decimal_places=4, null=True, blank=True)
    data_s = models.DateField("Действует с", null=True, blank=True)

    class Meta:
        db_table = "test_tarif"
