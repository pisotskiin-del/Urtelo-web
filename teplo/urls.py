from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

from accounts.views import LoginView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="abonents:index", permanent=False)),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("abonents/", include("abonents.urls")),
    path("catalogs/", include("catalogs.urls")),
    path("admin/", admin.site.urls),
]
