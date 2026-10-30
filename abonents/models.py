import gzip
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class MesArhiv(models.Model):
    """Архив закрытого месяца (в старой программе — файлы Arhiv\\PoMMГГГГ.dbf,
    DaMMГГГГ.dbf, OtMMГГГГ.dbf, taMMГГГГ.dbf). Хранит состояние таблиц на момент
    перехода на новый месяц; по нему можно отменить последний переход."""

    nom_mes = models.IntegerField("Месяц")
    god = models.IntegerField("Год")
    created = models.DateTimeField("Закрыт", auto_now_add=True)
    user = models.CharField("Кто закрыл", max_length=150, blank=True)
    potreb_count = models.IntegerField("Абонентов", default=0)
    nac_vsego = models.DecimalField("Начислено всего", max_digits=14, decimal_places=3, default=0)
    data = models.BinaryField("Таблицы (gzip JSON)")

    class Meta:
        verbose_name = "Архив месяца"
        verbose_name_plural = "Архив месяцев"
        ordering = ["-god", "-nom_mes", "-pk"]

    def __str__(self):
        return f"{self.nom_mes:02d}.{self.god}"

    def set_tables(self, tables):
        self.data = gzip.compress(json.dumps(tables, cls=DjangoJSONEncoder, ensure_ascii=False).encode())

    def tables(self):
        return json.loads(gzip.decompress(bytes(self.data)).decode())


UCHASTKI = [(1, "Рыбница"), (2, "Дубоссары"), (3, "Каменка")]


class Podpisant(models.Model):
    """Подписанты отчетов: кто утверждает, подписывает и исполняет. Запись
    без участка действует на все участки; запись с участком заменяет ее для
    этого участка (например, инспектор в отчетах по приборам учета)."""

    UTVERJDAU = "utv"
    VED_SPEC = "ved"
    ISPOLNITEL = "isp"
    PRIBORY = "pribor"
    ROLI = [
        (UTVERJDAU, "Утверждаю (гриф отчета)"),
        (VED_SPEC, "Подпись отчетов (ведущий специалист)"),
        (ISPOLNITEL, "Исполнитель"),
        (PRIBORY, "Отчеты по приборам учета (инспектор, контролер)"),
    ]

    rol = models.CharField("Где подписывает", max_length=10, choices=ROLI)
    # Код участка как в danrasch.cod_gorod. Не ссылка: dbf_import перезаливает
    # danrasch, и подписанты от этого не должны пропадать.
    gorod = models.IntegerField("Участок", null=True, blank=True,
                                choices=[(None, "Все участки")] + UCHASTKI)
    doljnost = models.CharField("Должность", max_length=200, blank=True)
    fio = models.CharField("Ф.И.О.", max_length=60, blank=True)

    class Meta:
        verbose_name = "Подписант документов"
        verbose_name_plural = "Подписанты документов"
        ordering = ["rol", "gorod", "pk"]

    def __str__(self):
        return f"{self.get_rol_display()}: {self.fio}"

    @classmethod
    def get(cls, rol, city=None):
        """(должность, Ф.И.О.) для роли и участка: сначала запись участка,
        затем общая."""
        rows = list(cls.objects.filter(rol=rol))
        code = getattr(city, "cod_gorod", None)
        p = next((r for r in rows if code is not None and r.gorod == code), None) or \
            next((r for r in rows if r.gorod is None), None)
        return ((p.doljnost or "").strip(), (p.fio or "").strip()) if p else ("", "")


class TarifGorod(models.Model):
    """Тарифы по участкам. В старой программе был один справочник tarif.dbf
    на все участки; здесь у каждого участка свои значения, а код тарифа тот
    же, что в tarif.dbf: по коду тариф берут отчеты и выгрузка в 1С."""

    # Код участка как в danrasch.cod_gorod (не ссылка, как у Podpisant).
    gorod = models.IntegerField("Участок", choices=UCHASTKI)
    id_tar = models.IntegerField("Код")
    name_tar = models.CharField("Наименование", max_length=30, blank=True)
    zn_tar = models.DecimalField("Тариф (Г)", max_digits=6, decimal_places=2, null=True, blank=True)
    diz_tar = models.DecimalField("Тариф (Д)", max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ["gorod", "id_tar"]
        constraints = [models.UniqueConstraint(fields=["gorod", "id_tar"], name="tarif_gorod_kod")]

    def __str__(self):
        return f"{self.get_gorod_display()}: {self.id_tar} {self.name_tar}".strip()

    @classmethod
    def dlya(cls, city):
        """{код: (тариф, тариф для дизеля)} участка. Кода, которого у участка
        нет, берется из общего справочника старой программы (tarif.dbf)."""
        from catalogs.models import Tarif
        code = getattr(city, "cod_gorod", city)
        out = {t.id_tar: (t.zn_tar or 0, t.diz_tar or 0) for t in Tarif.objects.exclude(id_tar=None)}
        out.update({t.id_tar: (t.zn_tar or 0, t.diz_tar or 0) for t in cls.objects.filter(gorod=code)})
        return out
