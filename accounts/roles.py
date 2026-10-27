"""Роли пользователей. Роль — это группа Django с набором прав на модели
приложения catalogs. Права создаются заново командой init_roles, поэтому
после перегенерации моделей её нужно запустить ещё раз."""

ADMIN = "Администратор"
OPERATOR = "Оператор"
VIEWER = "Наблюдатель"

# Какие действия разрешены каждой роли над справочниками.
ROLE_ACTIONS = {
    ADMIN: ("view", "add", "change", "delete"),
    OPERATOR: ("view", "add", "change"),
    VIEWER: ("view",),
}

# Ключи для командной строки: manage.py add_user ivanov --role operator
ROLE_KEYS = {"admin": ADMIN, "operator": OPERATOR, "viewer": VIEWER}


def user_roles(user):
    if not user.is_authenticated:
        return []
    names = list(user.groups.values_list("name", flat=True))
    if user.is_superuser and ADMIN not in names:
        names.insert(0, ADMIN)
    return names
