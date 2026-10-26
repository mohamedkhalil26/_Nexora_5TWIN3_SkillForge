from django.urls import path

from .views import (
    CertificatDetailView,
    CertificatListView,
    DemanderCertificatView,
    TelechargerCertificatView,
)

app_name = "certification"

urlpatterns = [
    path("", CertificatListView.as_view(), name="certificat-list"),
    path("<int:pk>/", CertificatDetailView.as_view(), name="certificat-detail"),
    path("<int:pk>/telecharger/", TelechargerCertificatView.as_view(), name="certificat-pdf"),
    path("demander/<slug:slug>/", DemanderCertificatView.as_view(), name="certificat-demander"),
]
