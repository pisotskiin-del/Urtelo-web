from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.roles import ADMIN, ROLE_KEYS


class Command(BaseCommand):
    help = "Создать пользователя с ролью: add_user ivanov --role operator --password ..."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("--role", choices=sorted(ROLE_KEYS), required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--name", default="", help="ФИО для отображения")

    def handle(self, *args, **opts):
        role = ROLE_KEYS[opts["role"]]
        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            raise CommandError("Роли ещё не созданы: выполните manage.py init_roles")
        user, created = get_user_model().objects.get_or_create(username=opts["username"])
        user.set_password(opts["password"])
        user.first_name = opts["name"] or user.first_name
        user.is_staff = role == ADMIN  # вход в админку только у администратора
        user.save()
        user.groups.set([group])
        self.stdout.write(f"{'Создан' if created else 'Обновлён'} пользователь {user.username}: {role}")
