"""Понятные сообщения вместо страницы с отладочным кодом.

- Недостаточно прав (PermissionDenied) — страница «Недостаточно прав».
- База не обновлена под новую версию программы (нет таблицы или колонки) —
  подсказка запустить update.bat.
Остальные ошибки показываются как обычно.
"""

from django.core.exceptions import PermissionDenied
from django.db import OperationalError, ProgrammingError
from django.shortcuts import render

NE_OBNOVLENA = ("no such column", "no such table", "has no column named")


class PonyatnyeOshibki:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return render(request, "oshibka.html", {
                "zagolovok": "Недостаточно прав",
                "tekst": "У вашей учётной записи нет прав на это действие. "
                         "Обратитесь к администратору программы.",
            }, status=403)
        if isinstance(exception, (OperationalError, ProgrammingError)) and \
                any(s in str(exception) for s in NE_OBNOVLENA):
            return render(request, "oshibka.html", {
                "zagolovok": "База данных не обновлена",
                "tekst": "Программа обновлена, а база данных ещё нет. Закройте программу "
                         "и запустите update.bat в папке программы, затем откройте её снова.",
                "podrobno": str(exception),
            }, status=500)
        return None
