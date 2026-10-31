"""Получить из КРЭДО показания приборов учёта за текущий месяц участка и
сохранить ответ (то же, что кнопка на странице «КРЭДО: показания приборов»).
В карты показания не записываются — разнос делается на странице.

    python manage.py kredo_pokazaniya --gorod 1
    python manage.py kredo_pokazaniya --gorod 1 --xml otvet.xml   # сохранить и сырой ответ
"""

from django.core.management.base import BaseCommand, CommandError

from abonents import kredo
from abonents.views import _kredo_poluchit


class Command(BaseCommand):
    help = "Приём показаний приборов учёта из КРЭДО (без записи в карты)"

    def add_arguments(self, parser):
        parser.add_argument("--gorod", type=int, required=True, help="код участка: 1 Рыбница, 2 Дубоссары, 3 Каменка")
        parser.add_argument("--xml", help="записать ответ сервиса в этот файл")

    def handle(self, gorod, xml=None, **opts):
        try:
            z = _kredo_poluchit(gorod, "manage.py")
        except kredo.KredoError as e:
            raise CommandError(str(e))
        if xml:
            with open(xml, "w", encoding="utf-8") as f:
                f.write(z.xml)
        stroki = kredo.sverit(kredo.razobrat(z.xml))
        self.stdout.write(f"Получено строк: {len(stroki)} (запись № {z.pk}, страница /abonents/kredo/{z.pk}/)")
        for k, t in kredo.STATUSY.items():
            n = sum(1 for s in stroki if s.status == k)
            if n:
                self.stdout.write(f"  {t}: {n}")
