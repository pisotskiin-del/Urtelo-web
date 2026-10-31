from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from accounts.roles import ADMIN, ROLE_ACTIONS


class Command(BaseCommand):
    help = "Создать или обновить роли (группы) и их права на справочники."

    def handle(self, *args, **opts):
        catalog_models = list(apps.get_app_config("catalogs").get_models()) + [apps.get_model("abonents", m) for m in ("Podpisant", "TarifGorod")]
        for role, actions in ROLE_ACTIONS.items():
            group, _ = Group.objects.get_or_create(name=role)
            perms = []
            for model in catalog_models:
                ct = ContentType.objects.get_for_model(model)
                codenames = [f"{a}_{model._meta.model_name}" for a in actions]
                perms += Permission.objects.filter(content_type=ct, codename__in=codenames)
            if role == ADMIN:
                # Администратор управляет и пользователями.
                perms += Permission.objects.filter(content_type__app_label="auth")
            group.permissions.set(perms)
            self.stdout.write(f"{role}: прав {len(perms)}")
