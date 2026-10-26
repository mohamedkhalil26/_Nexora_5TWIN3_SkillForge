"""URLs accounts (Ch5 : routes nommees, include() depuis config)."""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import InscriptionView, ProfilDetailView, ProfilUpdateView

app_name = "accounts"

urlpatterns = [
    path("inscription/", InscriptionView.as_view(), name="register"),
    path("connexion/", LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("deconnexion/", LogoutView.as_view(next_page="home"), name="logout"),
    path("profil/<int:pk>/", ProfilDetailView.as_view(), name="profil"),
    path("profil/<int:pk>/modifier/", ProfilUpdateView.as_view(), name="profil-update"),
]
