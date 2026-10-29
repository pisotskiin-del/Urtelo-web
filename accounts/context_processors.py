from .roles import user_roles
from .views import logo_path


def roles(request):
    return {"user_roles": user_roles(request.user), "logo": logo_path()}
