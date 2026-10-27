from django import forms
from django.db import models

from catalogs.models import Akcept, GvsKot, Kategorpot, Potreb

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


class KartaForm(forms.ModelForm):
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
        for name, field in self.fields.items():
            model_field = Potreb._meta.get_field(name)
            if isinstance(field, forms.CharField):
                field.empty_value = ""  # как при загрузке из DBF: пустая строка, а не NULL
                field.strip = False
            if isinstance(model_field, models.DateField) and not isinstance(model_field, models.DateTimeField):
                field.widget = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")

    class Meta:
        model = Potreb
        fields = []
        widgets = {"inf": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        data = super().clean()
        # Неизменённые поля сохраняются как были (с пробелами по краям и NULL),
        # чтобы «Сохранить» без правок не меняло запись.
        for name in self.fields:
            if name in data and name not in self.changed_data:
                data[name] = getattr(self.instance, name)
        # Как в старой форме: новое число дней перерасчета обнуляет коэффициент
        # и Гкал перерасчета, если их не исправили вместе с ним.
        if "dn_pereras" in self.changed_data:
            for name in ("tkf_perer", "gkl_perer"):
                if name in self.fields and name not in self.changed_data:
                    data[name] = 0
        return data


def karta_form(tab_key, *args, **kwargs):
    form_class = forms.modelform_factory(Potreb, form=KartaForm, fields=layout.editable_fields(tab_key))
    return form_class(*args, tab_key=tab_key, **kwargs)
