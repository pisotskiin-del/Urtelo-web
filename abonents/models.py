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
