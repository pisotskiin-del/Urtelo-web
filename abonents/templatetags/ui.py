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


@register.simple_tag
def static_v(path):
    """Ссылка на статический файл с меткой версии: после обновления программы
    окно сразу берёт новое оформление, без Ctrl+F5."""
    from django.conf import settings
    from django.templatetags.static import static
    try:
        version = int((settings.BASE_DIR / "static" / path).stat().st_mtime)
    except OSError:
        return static(path)
    return f"{static(path)}?v={version}"


@register.simple_tag
def rcell(value, col):
    """Значение ячейки отчета (abonents/reports.py) по типу колонки."""
    from django.utils import formats

    if value is None or value == "":
        return ""
    if col.kind == "num" and not isinstance(value, str):
        return formats.number_format(value, col.places, use_l10n=True, force_grouping=True)
    if col.kind == "date" and hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")
    return value


@register.filter
def withcols(row, cols):
    """Пары (значение, колонка) строки отчета."""
    return list(zip(row, cols))
