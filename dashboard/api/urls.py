from django.urls import path

from .views import mon_resume

app_name = "dashboard-api"

urlpatterns = [
    path("resume/", mon_resume, name="mon-resume"),
]
