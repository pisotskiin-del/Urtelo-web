"""Иконки интерфейса: {% load ui %} … {% icon "edit" %}. Сами рисунки — в
templates/_icons.html (набор SVG-символов, подключается в base.html)."""

from django import template
from django.utils.html import format_html

register = template.Library()

# Иконки разделов карты абонента по заголовку блока.
GROUP_ICONS = {
    "Способ расчёта": "sliders", "Потребление по прибору": "gauge",
    "Потребление по присоединённой нагрузке": "thermo", "Итоги": "chart", "Лимит и прочее": "shield",
    "Присоединённые объекты": "link", "Договор": "file", "Справочники": "book", "Здание и нагрузка": "building",
    "Руководство": "user", "Адрес юридический": "pin", "Адрес объекта": "pin", "Связь": "phone", "Банк": "bank",
    "Свидетельство о гос. регистрации": "badge", "Данные для акта отпущенной тепловой энергии": "file",
}
TAB_ICONS = {"otop": "flame", "gvs": "drop", "ishod": "file"}


@register.simple_tag
def icon(name, cls=""):
    return format_html('<svg class="i {}" aria-hidden="true"><use href="#i-{}"></use></svg>', cls, name)


@register.simple_tag
def group_icon(title):
    return icon(GROUP_ICONS.get(title, "list"))


@register.simple_tag
def tab_icon(key):
    return icon(TAB_ICONS.get(key, "list"))
