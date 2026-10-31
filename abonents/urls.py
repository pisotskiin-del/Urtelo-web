from django.urls import path

from . import views

app_name = "abonents"

urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.nov_abonent, name="new"),
    path("raschet/", views.raschet_view, name="raschet"),
    path("raschet/itog/", views.raschet_itog, name="raschet_itog"),
    path("raschet/itog/rasshifr/", views.raschet_rasshifr, name="raschet_rasshifr"),
    path("raschet/dannye/", views.dan_rasch, name="dan_rasch"),
    path("nov-mes/", views.nov_mes_view, name="nov_mes"),
    path("nov-mes/<int:pk>/1c/", views.abot_1c, name="abot_1c"),
    path("otchety/", views.otchety, name="otchety"),
    path("otchety/polez_otpusk/rasshifr/", views.polez_rasshifr, name="polez_rasshifr"),
    path("otchety/<slug:key>/", views.otchet, name="otchet"),
    path("<int:potreb_id>/", views.karta, name="karta"),
    path("<int:potreb_id>/edit/", views.karta_edit, name="edit"),
    path("<int:potreb_id>/delete/", views.karta_delete, name="delete"),
    path("<int:potreb_id>/prisoed/", views.prisoed, name="prisoed"),
    path("<int:potreb_id>/sposob/", views.sposob, name="sposob"),
    path("<int:potreb_id>/poteri/", views.poteri_view, name="poteri"),
    path("<int:potreb_id>/teploschetchik/", views.teplosch_view, name="teplosch"),
    path("dogovor/<int:cod_gor>/<int:nom_dog>/", views.dogovor, name="dogovor"),
    path("dogovor/<int:cod_gor>/<int:nom_dog>/<slug:vid>/", views.dokument, name="dokument"),
    path("dokumenty/", views.dokumenty, name="dokumenty"),
    path("rassylka/", views.rassylka, name="rassylka"),
    path("pisma/", views.pisma, name="pisma"),
    path("pisma/<int:pk>/pdf/", views.pismo_pdf, name="pismo_pdf"),
    path("kredo/", views.kredo_view, name="kredo"),
    path("kredo/<int:pk>/", views.kredo_priem, name="kredo_priem"),
]
