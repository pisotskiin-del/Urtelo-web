import gzip
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class MesArhiv(models.Model):
    """Архив закрытого месяца (в старой программе — файлы Arhiv\\PoMMГГГГ.dbf,
    DaMMГГГГ.dbf, OtMMГГГГ.dbf, taMMГГГГ.dbf). Хранит состояние таблиц на момент
    перехода на новый месяц; по нему можно отменить последний переход.
    Месяцы, закрытые в старой программе, загружаются из файлов Arhiv командой
    arhiv_import (источник «dbf»): они нужны отчетам за период, отменять их нельзя."""

    WEB, DBF = "web", "dbf"

    nom_mes = models.IntegerField("Месяц")
    god = models.IntegerField("Год")
    created = models.DateTimeField("Закрыт", auto_now_add=True)
    user = models.CharField("Кто закрыл", max_length=150, blank=True)
    potreb_count = models.IntegerField("Абонентов", default=0)
    nac_vsego = models.DecimalField("Начислено всего", max_digits=14, decimal_places=3, default=0)
    data = models.BinaryField("Таблицы (gzip JSON)")
    istochnik = models.CharField("Источник", max_length=3, default=WEB,
                                 choices=[(WEB, "Новая программа"), (DBF, "Архив старой программы")])

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
    AKT = "akt"
    ROLI = [
        (UTVERJDAU, "Утверждаю (гриф отчета)"),
        (VED_SPEC, "Подпись отчетов (ведущий специалист)"),
        (ISPOLNITEL, "Исполнитель"),
        (PRIBORY, "Отчеты по приборам учета (инспектор, контролер)"),
        (AKT, "Акт о потреблении: «в лице …» (должность и Ф.И.О. в родительном падеже)"),
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


class Nastroika(models.Model):
    """Настройки программы (одна запись), меняет Администратор в
    «Справочниках». Пока — папка для выгрузки в 1С."""

    papka_1c = models.CharField(
        "Папка для выгрузки в 1С", max_length=255, blank=True,
        help_text="Сюда при переходе на новый месяц записывается файл Abpt<ГГ><ММ>.dbf. "
                  "Пусто — файл только скачивается в «Закрытых месяцах».")

    class Meta:
        verbose_name = "Настройки программы"
        verbose_name_plural = "Настройки программы"
        ordering = ["pk"]

    def __str__(self):
        return "Настройки программы"

    @classmethod
    def papka(cls):
        """Папка для 1С: из настроек программы, иначе TEPLO_1C_DIR."""
        from django.conf import settings
        n = cls.objects.order_by("pk").first()
        return ((n.papka_1c if n else "") or getattr(settings, "TEPLO_1C_DIR", "") or "").strip()


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


class Pismo(models.Model):
    """Журнал отправки документов абонентам по почте (реестр отправленных
    писем reestrmail старой программы). Каждая попытка — запись: удачная или
    с текстом ошибки. Номер записи — номер документа в «Информации-счёте»;
    первый номер задается TEPLO_PISMO_NOMER (чтобы продолжить нумерацию
    старой программы)."""

    OK, OSHIBKA, PROVERKA = "ok", "err", "chk"
    POCHTA, KREDO = "mail", "kredo"

    nomer = models.IntegerField("Номер документа", unique=True)
    kanal = models.CharField("Куда", max_length=5, default=POCHTA,
                             choices=[(POCHTA, "Почта"), (KREDO, "КРЭДО")])
    created = models.DateTimeField("Отправлено", auto_now_add=True)
    user = models.CharField("Кто отправил", max_length=150, blank=True)
    cod_gor = models.IntegerField("Участок")
    nom_dog = models.IntegerField("Договор №")
    potreb_id = models.IntegerField("Л/№")
    name_potre = models.CharField("Потребитель", max_length=120, blank=True)
    email = models.CharField("Адрес", max_length=254, blank=True)
    vid = models.CharField("Документ", max_length=10)
    nom_mes = models.IntegerField("Месяц")
    god = models.IntegerField("Год")
    status = models.CharField("Результат", max_length=3,
                              choices=[(OK, "Отправлено"), (OSHIBKA, "Ошибка"), (PROVERKA, "Проверка (не отправлялось)")])
    oshibka = models.TextField("Ошибка", blank=True)
    otvet = models.TextField("Ответ КРЭДО", blank=True)
    fail = models.CharField("Файл PDF", max_length=500, blank=True)

    class Meta:
        verbose_name = "Отправленное письмо"
        verbose_name_plural = "Реестр отправленных писем"
        ordering = ["-pk"]

    def __str__(self):
        return f"№ {self.nomer} {self.name_potre} {self.nom_mes:02d}.{self.god}"

    @classmethod
    def sleduyushchij_nomer(cls):
        from django.conf import settings
        last = cls.objects.aggregate(m=models.Max("nomer"))["m"]
        return last + 1 if last else int(getattr(settings, "TEPLO_PISMO_NOMER", 1) or 1)


class KredoPriem(models.Model):
    """Полученные из КРЭДО показания приборов учёта (кнопки «Прием
    информации о последних показаниях…» и «Разнести…» формы rric). Ответ
    сервиса хранится целиком; при разносе записывается, что изменено."""

    KREDO, FAIL = "kredo", "fail"

    created = models.DateTimeField("Получено", auto_now_add=True)
    user = models.CharField("Кто получил", max_length=150, blank=True)
    cod_gor = models.IntegerField("Участок")
    nom_mes = models.IntegerField("Месяц")
    god = models.IntegerField("Год")
    istochnik = models.CharField("Источник", max_length=5, default=KREDO,
                                 choices=[(KREDO, "Сервис КРЭДО"), (FAIL, "Файл XML")])
    xml = models.TextField("Ответ сервиса")
    strok = models.IntegerField("Строк", default=0)
    razneseno = models.DateTimeField("Разнесено", null=True, blank=True)
    razn_user = models.CharField("Кто разнёс", max_length=150, blank=True)
    # JSON в текстовом поле: SQLite в Python для Windows бывает без расширения JSON1.
    izm = models.TextField("Изменения (JSON)", default="[]", blank=True)

    class Meta:
        verbose_name = "Показания из КРЭДО"
        verbose_name_plural = "Показания из КРЭДО"
        ordering = ["-pk"]

    def __str__(self):
        return f"{self.created:%d.%m.%Y %H:%M} участок {self.cod_gor}, {self.nom_mes:02d}.{self.god}"

    @property
    def izmeneniya(self):
        """[[л/№, было, стало, дата было, дата стало]] — что изменено при разносе."""
        import json
        try:
            return json.loads(self.izm or "[]")
        except ValueError:
            return []

    @izmeneniya.setter
    def izmeneniya(self, value):
        import json
        self.izm = json.dumps(value, ensure_ascii=False)
