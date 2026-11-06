from django.conf import settings
from django.contrib.auth import views as auth_views

# Логотип предприятия на заставке: положите файл logo.png (или logo.svg) в
# static/img. Пока его нет, показывается значок программы.
LOGO_FILES = ("img/zastavka.png", "img/logo.png", "img/logo.svg", "img/logo.jpg")


def logo_path():
    for name in LOGO_FILES:
        if (settings.BASE_DIR / "static" / name).exists():
            return name
    return "img/teplo.svg"


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        return super().get_context_data(logo=logo_path(), **kwargs)
