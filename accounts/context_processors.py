from .roles import user_roles


def roles(request):
    return {"user_roles": user_roles(request.user)}
