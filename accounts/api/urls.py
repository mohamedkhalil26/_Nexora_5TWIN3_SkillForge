from django.urls import path

from .views import liste_apprenants, mon_profil, suggerer_bio

app_name = "accounts-api"

urlpatterns = [
    path("profil/", mon_profil, name="mon-profil"),
    path("apprenants/", liste_apprenants, name="liste-apprenants"),
    path("suggerer-bio/", suggerer_bio, name="suggerer-bio"),
]
