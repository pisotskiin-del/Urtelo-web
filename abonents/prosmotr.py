"""Просмотр закрытого месяца («только просмотр»).

После перехода на новый месяц можно выбрать в верхней строке любой закрытый
месяц из архива (MesArhiv) и смотреть список абонентов, карточки, карты
договоров, итоги расчета, исходные данные, счета и акты так, как они были на
момент закрытия месяца. Выбранный месяц запоминается в сеансе пользователя
до возврата к текущему месяцу или выхода из программы.

Пока выбран закрытый месяц, программа ничего не меняет: middleware
ProsmotrMiddleware отклоняет все отправки форм (POST), кроме выбора месяца и
выхода, а страницы правки (изменить, удалить, новый абонент и т. п.)
открывают вместо себя карточку или список с подсказкой.
"""

import re
from collections import OrderedDict

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import resolve, Resolver404, reverse

from . import kopiya

KEY = "prosmotr_mes"  # "ГГГГ-ММ" в сеансе

# Страницы, где можно только менять данные: в просмотре — переход на карточку
# (если в адресе есть лицевой №) или на список абонентов.
PRAVKA = {"new", "edit", "delete", "pokazanie", "prisoed", "sposob", "poteri", "teplosch", "kredo_kod"}
# Отправки форм, которые разрешены и в просмотре.
RAZRESHENO_POST = {"prosmotr", "logout", "login"}

_cache = OrderedDict()  # {(pk, created): arhiv.Mesyac} — разбор архива дорогой


def _mesyac(arh):
    from . import arhiv
    key = (arh.pk, arh.created)
    m = _cache.get(key)
    if m is None:
        from .models import MesArhiv
        m = arhiv.Mesyac(MesArhiv.objects.get(pk=arh.pk))
        _cache[key] = m
        while len(_cache) > 4:
            _cache.popitem(last=False)
    else:
        _cache.move_to_end(key)
    return m


def razobrat(raw):
    """"ГГГГ-ММ" → (месяц, год) или None."""
    raw = (raw or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}", raw) or not 1 <= int(raw[5:]) <= 12:
        return None
    return int(raw[5:]), int(raw[:4])


def najti(raw):
    """Mesyac закрытого месяца по "ГГГГ-ММ" или None."""
    from . import arhiv
    key = razobrat(raw)
    if key is None:
        return None
    a = arhiv.zakrytye({key}).get(key)
    return _mesyac(a) if a else None


def vybran(request):
    """Просматриваемый закрытый месяц (arhiv.Mesyac) или None — текущий месяц."""
    if hasattr(request, "_prosmotr"):
        return request._prosmotr
    m = None
    session = getattr(request, "session", None)
    raw = session.get(KEY) if session is not None else None
    if raw:
        m = najti(raw)
        if m is None:   # месяц убрали из архива (отменили переход) — снова текущий
            session.pop(KEY, None)
    request._prosmotr = m
    return m


def get(request):
    """Закрытый месяц, который показывается по архиву MesArhiv (только
    абоненты и города), или None. Если у месяца есть полная копия данных
    (kopiya), все страницы и так читают из неё, и тогда здесь None."""
    m = vybran(request)
    if m is None or kopiya.est(m.mes, m.god):
        return None
    return m


def kod(m):
    return f"{m.god}-{m.mes:02d}" if m else ""


class ProsmotrMiddleware:
    """В просмотре закрытого месяца данные не меняются, а если есть полная копия
    месяца, все страницы читают данные из неё."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not request.session.get(KEY):
            return self.get_response(request)
        m = vybran(request)
        if m is None:
            return self.get_response(request)
        try:
            match = resolve(request.path_info)
        except Resolver404:
            return self.get_response(request)
        name = match.url_name
        est_kopiya = kopiya.est(m.mes, m.god)
        # С полной копией месяца потери и теплосчётчик можно посмотреть (без правки).
        pravka = match.app_name == "abonents" and name in PRAVKA and not (
            est_kopiya and name in ("poteri", "teplosch"))
        if request.method == "POST" and name not in RAZRESHENO_POST:
            messages.error(request, f"Открыт закрытый месяц {m.nazvanie} — только просмотр. "
                                    "Чтобы что-то изменить, вернитесь в текущий месяц.")
        elif pravka:
            messages.warning(request, f"Открыт закрытый месяц {m.nazvanie} — только просмотр.")
        else:
            alias = kopiya.otkryt(m.mes, m.god)
            if alias is None:
                return self.get_response(request)
            try:
                with kopiya.Vklyuchit(alias):
                    return self.get_response(request)
            finally:
                kopiya.zakryt(alias)
        if pravka:
            potreb_id = match.kwargs.get("potreb_id")
            return redirect(reverse("abonents:karta", args=[potreb_id]) if potreb_id else reverse("abonents:index"))
        return redirect(request.get_full_path())
