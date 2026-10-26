from django.urls import path

from .views import (
    annuler_reservation,
    detail_disponibilite,
    disponibilites,
    fiche_preparation,
    liste_mentors,
    reservations,
)

app_name = "mentoring-api"

urlpatterns = [
    path("mentors/", liste_mentors, name="liste-mentors"),
    path("disponibilites/", disponibilites, name="disponibilites"),
    path("disponibilites/<int:pk>/", detail_disponibilite, name="detail-disponibilite"),
    path("reservations/", reservations, name="reservations"),
    path("reservations/<int:pk>/annuler/", annuler_reservation, name="annuler-reservation"),
    path("fiche-preparation/", fiche_preparation, name="fiche-preparation"),
]
