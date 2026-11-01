"""Работа программы на сервере для нескольких компьютеров.

    .venv\\Scripts\\python server.py

Готовит оформление (collectstatic), применяет обновления базы (migrate) и
запускает веб-сервер waitress на всех сетевых адресах сервера, порт
TEPLO_SERVER_PORT (по умолчанию 8000). Сотрудники открывают http://<сервер>:8000/
или ярлык «Теплоснабжение» с TEPLO_SERVER в .env. Нужны пакеты из
requirements-server.txt и настройки DB_*, DJANGO_DEBUG=0, DJANGO_ALLOWED_HOSTS
в .env (см. README, «Работа на сервере»).
"""

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.chdir(BASE)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teplo.settings")
# Обмен с КРЭДО на общем сервере можно выключить строкой TEPLO_KREDO_ZDES=0 в .env
# (тогда КРЭДО — только из копии начальника, teplo.pyw через удалённый рабочий стол).


def main():
    import django
    from django.core.management import call_command
    django.setup()
    call_command("collectstatic", interactive=False, verbosity=0)
    call_command("migrate", verbosity=0)
    from waitress import serve
    from teplo.wsgi import application
    port = int(os.environ.get("TEPLO_SERVER_PORT", "8000"))
    print(f"Теплоснабжение: сервер работает на порту {port}. Не закрывайте это окно (или запустите как службу).")
    serve(application, host="0.0.0.0", port=port, threads=8)


if __name__ == "__main__":
    main()
