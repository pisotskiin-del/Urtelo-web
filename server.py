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
# Общий сервер работает в фоне: окно выбора сертификата для подписи документа КРЭДО
# никто не увидит, поэтому подпись здесь выключена (понятное сообщение вместо
# зависания). Подписывают в копии начальника (teplo.pyw через удалённый рабочий стол).
# Статусы, отзыв и показания из КРЭДО работают. Весь обмен выключает TEPLO_KREDO_ZDES=0.
os.environ.setdefault("TEPLO_KREDO_PODPIS", "0")


def main():
    import django
    from django.core.management import call_command
    django.setup()
    port = int(os.environ.get("TEPLO_SERVER_PORT", "8000"))
    # Защита от повторного запуска: если порт уже занят (сервер работает из
    # Планировщика или из другого окна server.bat), второй экземпляр не стартует.
    import socket
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            print(f"Сервер уже запущен: порт {port} занят. Второй экземпляр не запускается.")
            print("Остановить работающий сервер: stop-server.bat (от имени администратора).")
            return
    except OSError:
        pass
    # clear=True: файлы из архива обновления сохраняют старую дату, и без очистки
    # collectstatic считал бы прежнюю копию новее и не обновлял её.
    call_command("collectstatic", interactive=False, clear=True, verbosity=0)
    call_command("migrate", verbosity=0)
    from waitress import serve
    from teplo.wsgi import application
    print(f"Теплоснабжение: сервер работает на порту {port}. Не закрывайте это окно (или запустите как службу).")
    serve(application, host="0.0.0.0", port=port, threads=8)


if __name__ == "__main__":
    main()
