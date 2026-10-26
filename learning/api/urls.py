from django.urls import path

from .views import (
    detail_cours,
    detail_module,
    detail_ressource,
    generer_description,
    generer_image,
    liste_competences,
    liste_cours,
    modules,
    ressources,
)

app_name = "learning-api"

urlpatterns = [
    path("competences/", liste_competences, name="liste-competences"),
    path("cours/", liste_cours, name="liste-cours"),
    path("cours/<slug:slug>/", detail_cours, name="detail-cours"),
    path("modules/", modules, name="modules"),
    path("modules/<int:pk>/", detail_module, name="detail-module"),
    path("ressources/", ressources, name="ressources"),
    path("ressources/<int:pk>/", detail_ressource, name="detail-ressource"),
    path("generer-description/", generer_description, name="generer-description"),
    path("generer-image/", generer_image, name="generer-image"),
]
