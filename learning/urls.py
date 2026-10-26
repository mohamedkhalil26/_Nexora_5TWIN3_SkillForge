from django.urls import path

from .views import (
    CompetenceCreateView,
    CompetenceDeleteView,
    CompetenceDetailView,
    CompetenceListView,
    CompetenceUpdateView,
    CoursCreateView,
    CoursDeleteView,
    CoursDetailView,
    CoursListView,
    CoursUpdateView,
    ModuleCreateView,
    ModuleDeleteView,
    ModuleDetailView,
    ModuleUpdateView,
    RessourceCreateView,
    RessourceDeleteView,
    RessourceUpdateView,
)

app_name = "learning"

urlpatterns = [
    path("competences/", CompetenceListView.as_view(), name="competence-list"),
    path("competences/nouvelle/", CompetenceCreateView.as_view(), name="competence-create"),
    path(
        "competences/<slug:slug>/modifier/",
        CompetenceUpdateView.as_view(),
        name="competence-update",
    ),
    path(
        "competences/<slug:slug>/supprimer/",
        CompetenceDeleteView.as_view(),
        name="competence-delete",
    ),
    path("competences/<slug:slug>/", CompetenceDetailView.as_view(), name="competence-detail"),
    path("cours/", CoursListView.as_view(), name="cours-list"),
    path("cours/nouveau/", CoursCreateView.as_view(), name="cours-create"),
    path("cours/<slug:slug>/", CoursDetailView.as_view(), name="cours-detail"),
    path("cours/<slug:slug>/modifier/", CoursUpdateView.as_view(), name="cours-update"),
    path("cours/<slug:slug>/supprimer/", CoursDeleteView.as_view(), name="cours-delete"),
    path("modules/nouveau/", ModuleCreateView.as_view(), name="module-create"),
    path("modules/<int:pk>/", ModuleDetailView.as_view(), name="module-detail"),
    path("modules/<int:pk>/modifier/", ModuleUpdateView.as_view(), name="module-update"),
    path("modules/<int:pk>/supprimer/", ModuleDeleteView.as_view(), name="module-delete"),
    path("ressources/nouvelle/", RessourceCreateView.as_view(), name="ressource-create"),
    path(
        "ressources/<int:pk>/modifier/",
        RessourceUpdateView.as_view(),
        name="ressource-update",
    ),
    path(
        "ressources/<int:pk>/supprimer/",
        RessourceDeleteView.as_view(),
        name="ressource-delete",
    ),
]
