from django.urls import path

from .views import (
    ConfirmerReservationView,
    DisponibiliteCreateView,
    DisponibiliteDeleteView,
    DisponibiliteUpdateView,
    EnvoyerMessageView,
    MentorDetailView,
    MentorListView,
    MesReservationsView,
    MonProfilMentorView,
    ReservationDetailView,
    ReserverView,
)

app_name = "mentoring"

urlpatterns = [
    path("", MentorListView.as_view(), name="mentor-list"),
    path("mon-profil/", MonProfilMentorView.as_view(), name="mon-profil"),
    path("disponibilites/nouvelle/", DisponibiliteCreateView.as_view(), name="dispo-create"),
    path(
        "disponibilites/<int:pk>/modifier/",
        DisponibiliteUpdateView.as_view(),
        name="dispo-update",
    ),
    path(
        "disponibilites/<int:pk>/supprimer/",
        DisponibiliteDeleteView.as_view(),
        name="dispo-delete",
    ),
    path("mes-reservations/", MesReservationsView.as_view(), name="mes-reservations"),
    path("mentors/<int:pk>/", MentorDetailView.as_view(), name="mentor-detail"),
    path("reserver/<int:dispo_pk>/", ReserverView.as_view(), name="reserver"),
    path("reservations/<int:pk>/", ReservationDetailView.as_view(), name="reservation-detail"),
    path(
        "reservations/<int:pk>/confirmer/",
        ConfirmerReservationView.as_view(),
        name="reservation-confirmer",
    ),
    path(
        "reservations/<int:pk>/message/",
        EnvoyerMessageView.as_view(),
        name="reservation-message",
    ),
]
