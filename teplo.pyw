"""Запуск «Теплоснабжения» как обычной программы.

Двойной щелчок по ярлыку «Теплоснабжение» запускает сервер без окна консоли и
открывает приложение в отдельном окне Microsoft Edge (или Chrome, Яндекс Браузера) без
адресной строки и вкладок. Когда окно приложения закрыто, сервер
останавливается. Если сервер уже работает (например, через run.bat), просто
открывается окно.

    pythonw teplo.pyw              — запустить
    python teplo.pyw --shortcut    — создать ярлыки на рабочем столе и в меню «Пуск»

На сервере, где через удалённый рабочий стол работают несколько операторов, в .env
пишется TEPLO_PORT=auto. Тогда у каждого оператора запускается своя копия сервера
на свободном порту под его учётной записью (подпись в КРЭДО — его сертификатом), а
профиль окна и журнал лежат в его папке %LOCALAPPDATA%\\Teplo.
"""

import base64
import os
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent


def _dotenv(name):
    """Значение из .env рядом с программой (переменная окружения важнее)."""
    if name in os.environ:
        return os.environ[name]
    try:
        for line in (BASE / ".env").read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.partition("=")
            if sep and not line.lstrip().startswith("#") and key.strip() == name:
                return value.strip().strip('"')
    except OSError:
        pass
    return ""


def _user_dir():
    root = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    path = Path(root) / "Teplo"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _port_alive(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


# TEPLO_PORT=auto — у каждого пользователя Windows своя копия сервера (см. выше).
AUTO = _dotenv("TEPLO_PORT").strip().lower() == "auto"
if AUTO:
    USER_DIR = _user_dir()
    PORT_FILE = USER_DIR / "port"
    try:
        PORT = int(PORT_FILE.read_text().strip())
    except (OSError, ValueError):
        PORT = 0
    if not PORT or not _port_alive(PORT):
        PORT = _free_port()
    LOG = USER_DIR / "teplo.log"
    PROFILE = USER_DIR / "app-profile"
else:
    PORT = int(_dotenv("TEPLO_PORT") or "8000")
    PORT_FILE = None
    LOG = BASE / "teplo.log"
    PROFILE = BASE / ".app-profile"
# TEPLO_SERVER=http://server-ff:8000/ — программа работает на сервере: ярлык только
# открывает её окно, своя копия на этом компьютере не запускается.
SERVER = _dotenv("TEPLO_SERVER").rstrip("/")
URL = SERVER + "/" if SERVER else f"http://127.0.0.1:{PORT}/"
TITLE = "Теплоснабжение"
WINDOWS = sys.platform == "win32"


def message(text):
    if WINDOWS:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, text, TITLE, 0x10)
    else:
        print(text, file=sys.stderr)


def server_running():
    return _port_alive(PORT)


def python_exe():
    """python.exe из .venv (с консолью не открывается: окно скрыто флагом)."""
    venv = BASE / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
    if venv.exists():
        return str(venv)
    exe = Path(sys.executable)
    console = exe.with_name("python.exe")
    return str(console if exe.name.lower() == "pythonw.exe" and console.exists() else exe)


def start_server():
    log = open(LOG, "a", encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if WINDOWS else 0
    server = subprocess.Popen(
        [python_exe(), "manage.py", "runserver", "--noreload", f"127.0.0.1:{PORT}"],
        cwd=BASE, stdout=log, stderr=subprocess.STDOUT, creationflags=flags,
    )
    for _ in range(120):
        if server_running():
            if PORT_FILE:
                PORT_FILE.write_text(str(PORT))
            return server
        if server.poll() is not None:
            break
        time.sleep(0.25)
    server.kill()
    message(f"Сервер не запустился. Подробности в файле\n{LOG}")
    sys.exit(1)


def find_browser():
    names = ["msedge", "chrome"]
    roots = [os.environ.get(v) for v in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData")]
    places = [
        r"Microsoft\Edge\Application\msedge.exe",
        r"Google\Chrome\Application\chrome.exe",
        r"Yandex\YandexBrowser\Application\browser.exe",
    ]
    for root in filter(None, roots):
        for place in places:
            path = Path(root) / place
            if path.exists():
                return str(path)
    for name in names + ["google-chrome", "chromium", "chromium-browser"]:
        found = shutil.which(name)
        if found:
            return found
    return None


def open_window():
    """Окно приложения. Возвращает True, если дождались его закрытия."""
    browser = find_browser()
    if not browser:
        webbrowser.open(URL)
        return False
    # Отдельный профиль: окно живёт своим процессом (его закрытие видно) и
    # помнит вход пользователя.
    window = subprocess.Popen([
        browser, f"--app={URL}", f"--user-data-dir={PROFILE}", "--no-first-run",
        "--no-default-browser-check", "--start-maximized",
    ])
    window.wait()
    return True


def make_shortcuts():
    if not WINDOWS:
        print("Ярлыки создаются только в Windows")
        return
    pythonw = BASE / ".venv" / "Scripts" / "pythonw.exe"
    if not pythonw.exists():
        pythonw = Path(sys.executable).with_name("pythonw.exe")
    icon = BASE / "static" / "img" / "teplo.ico"
    script = f"""
$sh = New-Object -ComObject WScript.Shell
foreach ($dir in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {{
  $lnk = $sh.CreateShortcut((Join-Path $dir '{TITLE}.lnk'))
  $lnk.TargetPath = '{pythonw}'
  $lnk.Arguments = '"{BASE / "teplo.pyw"}"'
  $lnk.WorkingDirectory = '{BASE}'
  $lnk.IconLocation = '{icon}'
  $lnk.Description = '{TITLE}'
  $lnk.Save()
}}
"""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode()
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded], check=True)
    print("Ярлык «Теплоснабжение» создан на рабочем столе и в меню «Пуск».")


def main():
    if "--shortcut" in sys.argv:
        make_shortcuts()
        return
    if SERVER:
        open_window()
        return
    server = None if server_running() else start_server()
    try:
        waited = open_window()
        if not waited and server is not None:
            message("Приложение открыто в браузере. Нажмите OK, когда закончите работу: сервер остановится.")
    finally:
        if server is not None:
            server.terminate()
            if PORT_FILE:
                try:
                    PORT_FILE.unlink()
                except OSError:
                    pass


if __name__ == "__main__":
    main()
