"""Tests dashboard — Tache prio #1 : home par role, API resume, insight IA."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .ai import insight_apprenant, stats_plateforme

User = get_user_model()


class DashboardTests(TestCase):
    def test_home_anonyme_redirige(self):
        r = self.client.get(reverse("dashboard:home"))
        self.assertEqual(r.status_code, 302)

    def test_home_apprenant_avec_insight(self):
        user = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        self.client.force_login(user)
        r = self.client.get(reverse("dashboard:home"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("insight_ia", r.context)

    def test_api_resume_apprenant(self):
        user = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        self.client.force_login(user)
        r = self.client.get(reverse("dashboard-api:mon-resume"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["role"], "apprenant")

    def test_api_resume_anonyme_403(self):
        r = self.client.get(reverse("dashboard-api:mon-resume"))
        self.assertEqual(r.status_code, 403)

    def test_insight_et_stats(self):
        self.assertIn("quiz", insight_apprenant({"quiz_passes": 0, "moyenne": 0, "progression": 0}).lower())
        stats = stats_plateforme()
        for cle in ("utilisateurs", "cours", "tentatives", "certificats"):
            self.assertIn(cle, stats)
