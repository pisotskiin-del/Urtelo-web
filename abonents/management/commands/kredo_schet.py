"""Подписать «Информацию-счёт» по договору и (без --proverka) отправить в КРЭДО.

    python manage.py kredo_schet --gorod 1 --dog 19 --proverka   # только подписать, XML рядом с PDF
    python manage.py kredo_schet --gorod 1 --dog 19              # подписать и отправить
"""

from django.core.management.base import BaseCommand, CommandError

from abonents import documents, kredo_dok
from abonents.views import _dok_context


class Command(BaseCommand):
    help = "Подписанная «Информация-счёт» в КРЭДО по одному договору"

    def add_arguments(self, parser):
        parser.add_argument("--gorod", type=int, required=True)
        parser.add_argument("--dog", type=int, required=True, help="№ договора")
        parser.add_argument("--proverka", action="store_true", help="только подписать, не отправлять")

    def handle(self, gorod, dog, proverka, **opts):
        dok = documents.sobrat(gorod, dog)
        if dok is None:
            raise CommandError("В договоре нет действующих лицевых")
        z = kredo_dok.otpravit(dok, _dok_context(dok), "manage.py", proverka=proverka)
        self.stdout.write(f"№ {z.nomer}: {z.get_status_display()}. {z.oshibka}")
        if z.fail:
            self.stdout.write(f"PDF: {z.fail}")
        if z.otvet:
            self.stdout.write(f"Ответ КРЭДО: {z.otvet[:500]}")
        if z.status == z.OSHIBKA:
            raise CommandError("Не получилось")
