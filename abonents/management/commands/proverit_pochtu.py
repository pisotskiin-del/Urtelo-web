"""Проверить соединение с почтовым сервером из «Настроек рассылки писем»
и показать полный текст ошибки (письмо не отправляется).

    python manage.py proverit_pochtu
"""

import ssl

from django.core.management.base import BaseCommand

from abonents import pochta


class Command(BaseCommand):
    help = "Проверить соединение с почтовым сервером (письмо не отправляется)."

    def handle(self, *args, **opts):
        s = pochta.nastrojki()
        if s is None:
            self.stdout.write(self.style.ERROR("Не заполнены «Настройки рассылки писем»"))
            return
        self.stdout.write(f"Сервер: {(s.smtp or '').strip()}, порт {s.port or 25}, "
                          f"шифрование: {'да' if s.puses else 'нет'}, вход: {'да' if s.paunt else 'нет'}")
        conn = pochta.connection()
        try:
            conn.open()
        except ssl.SSLCertVerificationError as e:
            self.stdout.write(self.style.ERROR(f"Сертификат не прошёл проверку: {e.verify_message} (код {e.verify_code})"))
            self.stdout.write(str(e))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"{type(e).__name__}: {e}"))
            return
        conn.close()
        self.stdout.write(self.style.SUCCESS("Соединение и вход прошли успешно"))
