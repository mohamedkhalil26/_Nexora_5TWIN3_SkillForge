from django.urls import path

from .views import demander, eligibilite, mes_certificats

app_name = "certification-api"

urlpatterns = [
    path("", mes_certificats, name="mes-certificats"),
    path("eligibilite/<slug:slug>/", eligibilite, name="eligibilite"),
    path("demander/<slug:slug>/", demander, name="demander"),
]
