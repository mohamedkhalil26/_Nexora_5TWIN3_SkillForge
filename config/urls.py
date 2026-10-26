"""Routage racine (Ch1/Ch5 : include() des urls de chaque app + APIs DRF)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from dashboard.views import LandingView

urlpatterns = [
    path("", LandingView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("comptes/", include("accounts.urls")),
    path("apprendre/", include("learning.urls")),
    path("quiz/", include("quizzes.urls")),
    path("mentorat/", include("mentoring.urls")),
    path("certificats/", include("certification.urls")),
    path("tableau-de-bord/", include("dashboard.urls")),
    # API REST (workshop) : /api/<app>/...
    path("api/comptes/", include("accounts.api.urls")),
    path("api/apprendre/", include("learning.api.urls")),
    path("api/quiz/", include("quizzes.api.urls")),
    path("api/mentorat/", include("mentoring.api.urls")),
    path("api/certificats/", include("certification.api.urls")),
    path("api/dashboard/", include("dashboard.api.urls")),
]

admin.site.site_header = "SkillForge — Administration"
admin.site.site_title = "SkillForge Admin"
admin.site.index_title = "Back-office de la plateforme"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
