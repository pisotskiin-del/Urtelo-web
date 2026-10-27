from django.urls import path

from . import views

app_name = "catalogs"

urlpatterns = [
    path("", views.index, name="index"),
    path("<slug:slug>/", views.object_list, name="list"),
    path("<slug:slug>/new/", views.object_edit, name="create"),
    path("<slug:slug>/<int:pk>/", views.object_detail, name="detail"),
    path("<slug:slug>/<int:pk>/edit/", views.object_edit, name="edit"),
    path("<slug:slug>/<int:pk>/delete/", views.object_delete, name="delete"),
]
