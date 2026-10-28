from decimal import ROUND_HALF_UP, Decimal

from django import forms
from django.db import models

from catalogs.models import Akcept, Bank, Danrasch, GvsKot, Kategorpot, Minist, Potreb, SpDiametr, SpTeplosch, SpTeplpoteri

from . import layout


def _labels(tab_key):
    _, _, groups = layout.tab(tab_key)
    labels = {}
    for f in layout.HEADER + [f for _, fields in groups for f in fields]:
        labels.setdefault(f.name, f.label)
    return labels


def _choice_field(choices, current, label):
    """Выбор из списка; значение, которого нет в справочнике, не теряется."""
    choices = [(str(k), v) for k, v in choices]
    if current not in (None, "") and str(current) not in {k for k, _ in choices}:
        choices.append((str(current), f"код {current} (нет в справочнике)"))
    return forms.TypedChoiceField(
        label=label, choices=[("", "—")] + choices, coerce=int, empty_value=None, required=False,
    )


class DbfFormMixin:
    """Общие правила форм над таблицами из DBF: пустой текст хранится как "",
    пробелы по краям не срезаются, даты вводятся календарём, а поля, которые
    не меняли, сохраняются как были (с пробелами и NULL)."""

    def setup_dbf_fields(self):
        for name, field in self.fields.items():
            if name not in self._meta.fields:
                continue
            model_field = self._meta.model._meta.get_field(name)
            if isinstance(field, forms.CharField):
                field.empty_value = ""
                field.strip = False
            if isinstance(model_field, models.DateField) and not isinstance(model_field, models.DateTimeField):
                field.widget = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

    def keep_unchanged(self, data):
        if self.instance.pk is None:
            return data
        for name in self._meta.fields:
            if name in data and name not in self.changed_data:
                data[name] = getattr(self.instance, name)
        return data


class KartaForm(DbfFormMixin, forms.ModelForm):
    """Правка карты абонента: шапка и одна вкладка."""

    def __init__(self, *args, tab_key, **kwargs):
        super().__init__(*args, **kwargs)
        labels = _labels(tab_key)
        obj = self.instance
        for name, field in list(self.fields.items()):
            if name in labels:
                field.label = labels[name]
        lookups = {
            "id_kategor": lambda: Kategorpot.objects.order_by("id_kotegor").values_list("id_kotegor", "name_kateg"),
            "id_koteln": lambda: GvsKot.objects.filter(kod_gor=obj.cod_gor_id).order_by("name_kot")
                                                .values_list("id_kot", "name_kot"),
        }
        for name in self.fields:
            if name in layout.CHOICES:
                self.fields[name] = _choice_field(layout.CHOICES[name], getattr(obj, name), labels.get(name))
            elif name in lookups:
                self.fields[name] = _choice_field(lookups[name](), getattr(obj, name), labels.get(name))
        if "accept" in self.fields:
            # Акцепт обязателен и только из справочника akcept: 0 и пусто не допускаются.
            self.fields["accept"] = forms.TypedChoiceField(
                label=labels.get("accept"), coerce=int,
                choices=[(str(k), v) for k, v in Akcept.objects.order_by("id_akc").values_list("id_akc", "name_akc")],
            )
        if "cod_minist" in self.fields:
            self.fields["cod_minist"].queryset = self.fields["cod_minist"].queryset.order_by("name_minis")
        self.setup_dbf_fields()

    class Meta:
        model = Potreb
        fields = []
        widgets = {"inf": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        data = self.keep_unchanged(super().clean())
        # Как в старой форме: новое число дней перерасчета обнуляет коэффициент
        # и Гкал перерасчета, если их не исправили вместе с ним.
        if "dn_pereras" in self.changed_data:
            for name in ("tkf_perer", "gkl_perer"):
                if name in self.fields and name not in self.changed_data:
                    data[name] = 0
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if "id_koteln" in self.changed_data:
            # Как форма nov_abonent: название котельной хранится и в самой записи.
            kotel = GvsKot.objects.filter(id_kot=obj.id_koteln).first()
            obj.name_kot = kotel.name_kot if kotel else ""
        if commit:
            obj.save()
        return obj


def karta_form(tab_key, *args, **kwargs):
    form_class = forms.modelform_factory(Potreb, form=KartaForm, fields=layout.editable_fields(tab_key))
    return form_class(*args, tab_key=tab_key, **kwargs)


class PoteriForm(DbfFormMixin, forms.ModelForm):
    """Диаметр и длина шести участков (форма kalcul_poteri)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        diametrs = [(d, f"{d} мм") for d in SpDiametr.objects.order_by("diametr").values_list("diametr", flat=True)]
        for i in range(1, 7):
            self.fields[f"diametr{i}"] = _choice_field(diametrs, getattr(self.instance, f"diametr{i}"), "Диаметр")
            self.fields[f"dlina{i}"].label = "Длина"
        self.setup_dbf_fields()

    class Meta:
        model = SpTeplpoteri
        fields = [f"{name}{i}" for i in range(1, 7) for name in ("diametr", "dlina")]

    def clean(self):
        return self.keep_unchanged(super().clean())


class TeploschForm(DbfFormMixin, forms.ModelForm):
    """Информация по теплосчетчику (форма teploschetchik)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_dbf_fields()

    class Meta:
        model = SpTeplosch
        fields = ["name_obek", "adres_obek", "data_zapus", "nomer_prib", "tip_prib",
                  "ndata_pov", "kdata_pov", "mesto_ust", "mesto_ustp"]
        labels = {
            "name_obek": "Наименование объекта", "adres_obek": "Адрес объекта",
            "data_zapus": "Дата допуска в эксплуатацию", "nomer_prib": "№ устройства",
            "tip_prib": "Тип прибора учета", "ndata_pov": "Срок поверки от", "kdata_pov": "Срок поверки до",
            "mesto_ust": "Место установки", "mesto_ustp": "Место установки и № пломбы",
        }

    def clean(self):
        return self.keep_unchanged(super().clean())


class NovAbonentForm(DbfFormMixin, forms.ModelForm):
    """Ввод нового абонента (форма nov_abonent)."""

    def __init__(self, *args, city=None, **kwargs):
        super().__init__(*args, **kwargs)
        cities = Danrasch.objects.exclude(cod_gorod=None).order_by("cod_gorod")
        self.fields["cod_gor"] = forms.TypedChoiceField(
            label="Город", coerce=int, initial=city,
            choices=[(c.cod_gorod, c.name_gorod) for c in cities],
        )
        self.fields["nom_dog"].required = True
        self.fields["cod_minist"].queryset = Minist.objects.order_by("name_minis")
        self.fields["cod_minist"].empty_label = "—"
        self.fields["cod_banka"] = _choice_field(
            Bank.objects.order_by("name_banka").values_list("cod_banka", "name_banka"), None, "Банк")
        self.fields["id_kategor"] = _choice_field(
            Kategorpot.objects.order_by("id_kotegor").values_list("id_kotegor", "name_kateg"), None,
            "Категория потребителя")
        kotels = GvsKot.objects.order_by("kod_gor", "name_kot").values_list("id_kot", "name_kot", "kod_gor")
        self.fields["id_koteln"] = _choice_field([(k, n) for k, n, _ in kotels], None, "Котельная")
        self.kotel_city = {str(k): g for k, _, g in kotels}
        self.order_fields(["cod_gor"])
        self.setup_dbf_fields()

    class Meta:
        model = Potreb
        fields = ["nom_dog", "inf_pribor", "data_dog", "name_potre", "glav_potre", "adres_regi", "adres_sd",
                  "telefon", "fax", "direktor", "byhalter", "ras_chet", "kor_chet", "fisk_cod", "cod_banka",
                  "cod_minist", "id_kategor", "id_koteln"]
        labels = {
            "nom_dog": "№ договора", "inf_pribor": "№ счетчика", "data_dog": "Дата договора",
            "name_potre": "Имя потребителя", "glav_potre": "Главный потребитель",
            "adres_regi": "Адрес юридический", "adres_sd": "Адрес объекта", "telefon": "№ телефона",
            "fax": "№ факса", "direktor": "Директор", "byhalter": "Бухгалтер", "ras_chet": "Расчетный счет",
            "kor_chet": "Кор-счет", "fisk_cod": "Фискальный код", "cod_minist": "Министерство",
        }

    def clean(self):
        data = super().clean()
        kotel, city = data.get("id_koteln"), data.get("cod_gor")
        if kotel and self.kotel_city.get(str(kotel)) != city:
            self.add_error("id_koteln", "Котельная из другого города")
        return data

    def save(self, commit=True):
        p = super().save(commit=False)
        # Как APPEND BLANK в старой программе: пустые числа — 0, текст — пустая строка.
        for f in Potreb._meta.concrete_fields:
            if f.primary_key or f.is_relation or getattr(p, f.attname) is not None:
                continue
            if isinstance(f, (models.IntegerField, models.DecimalField)):
                setattr(p, f.attname, 0)
            elif isinstance(f, (models.CharField, models.TextField)):
                setattr(p, f.attname, "")
        p.cod_gor_id = self.cleaned_data["cod_gor"]
        p.accept = 1  # «Акцепт» 0 не допускается
        kotel = GvsKot.objects.filter(id_kot=p.id_koteln).first() if p.id_koteln else None
        p.name_kot = kotel.name_kot if kotel else ""
        last = Potreb.objects.order_by("-potreb_id").values_list("potreb_id", flat=True).first() or 0
        p.potreb_id = last + 1
        if commit:
            p.save()
        return p


class DanRaschForm(DbfFormMixin, forms.ModelForm):
    """Исходные данные для расчета по городу (форма dan_rasch)."""

    dnotop_vsem = forms.BooleanField(label="Записать дни отопления всем абонентам города", required=False)
    dngvs_vsem = forms.BooleanField(label="Записать дни ГВС всем абонентам города", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_dbf_fields()

    class Meta:
        model = Danrasch
        fields = ["t_vozd", "t_proekt", "dnotop", "dngvs", "qpfakt"]
        labels = {
            "t_vozd": "Фактическая t наружного воздуха, °С", "t_proekt": "Расчетная t для проектирования, °С",
            "dnotop": "Количество дней подачи отопления", "dngvs": "Количество дней подачи ГВС",
            "qpfakt": "Q факт, Гкал",
        }

    def clean(self):
        data = self.keep_unchanged(super().clean())
        if data.get("t_proekt") == 18:
            self.add_error("t_proekt", "Расчетная t не может быть 18 °С: на неё делится температурный коэффициент")
        return data

    def save(self, commit=True):
        d = super().save(commit=False)
        # Кнопка «сохранить» старой формы: t коэффициент = (18 − t факт) / (18 − t расчетная).
        if d.t_vozd is not None and d.t_proekt not in (None, 18):
            d.tkoef = ((Decimal(18) - d.t_vozd) / (Decimal(18) - d.t_proekt)).quantize(
                Decimal("0.001"), rounding=ROUND_HALF_UP)
        if commit:
            d.save()
        return d
