from django.urls import path

from . import views

app_name = "abonents"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:potreb_id>/", views.karta, name="karta"),
    path("<int:potreb_id>/edit/", views.karta_edit, name="edit"),
    path("<int:potreb_id>/delete/", views.karta_delete, name="delete"),
    path("dogovor/<int:cod_gor>/<int:nom_dog>/", views.dogovor, name="dogovor"),
]
