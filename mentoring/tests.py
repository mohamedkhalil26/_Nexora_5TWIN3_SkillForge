"""Tests mentoring — Tache prio #1 : resa protege le creneau, matching IA."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from learning.models import Competence

from .ai import recommander_mentors, score_mentor
from .models import Disponibilite, MentorProfile, Reservation

User = get_user_model()


class MentoringTests(TestCase):
    def setUp(self):
        self.mentor = User.objects.create_user(username="m", password="x", email="m@ex.tn", role="mentor")
        self.app = User.objects.create_user(
            username="a", password="x", email="a@ex.tn", objectifs="apprendre Django"
        )
        self.comp = Competence.objects.create(nom="Django", description="framework web", slug="dj")
        self.profil = MentorProfile.objects.create(mentor=self.mentor, verifie=True)
        self.profil.specialites.add(self.comp)
        debut = timezone.now() + timedelta(days=1)
        self.dispo = Disponibilite.objects.create(
            mentor=self.profil, debut=debut, fin=debut + timedelta(hours=1)
        )

    def test_reservation_marque_creneau(self):
        self.client.force_login(self.app)
        r = self.client.post(
            reverse("mentoring:reserver", args=[self.dispo.pk]), {"sujet": "aide vues"}
        )
        self.assertEqual(r.status_code, 302)
        self.dispo.refresh_from_db()
        self.assertTrue(self.dispo.reserve)
        resa = Reservation.objects.get(apprenant=self.app)
        self.assertEqual(resa.statut, "en_attente")

    def test_double_reservation_impossible(self):
        self.client.force_login(self.app)
        self.client.post(reverse("mentoring:reserver", args=[self.dispo.pk]), {"sujet": "x"})
        r = self.client.post(reverse("mentoring:reserver", args=[self.dispo.pk]), {"sujet": "y"})
        self.assertEqual(r.status_code, 404)  # creneau reserve : get_or_404
        self.assertEqual(Reservation.objects.filter(apprenant=self.app).count(), 1)

    def test_matching_ia(self):
        self.assertGreater(score_mentor(self.app, self.profil), 0)
        self.assertEqual(recommander_mentors(self.app, [self.profil]), [self.profil])

    def test_confirmation_genere_lien(self):
        self.client.force_login(self.app)
        self.client.post(reverse("mentoring:reserver", args=[self.dispo.pk]), {"sujet": "x"})
        resa = Reservation.objects.get(apprenant=self.app)
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("mentoring:reservation-confirmer", args=[resa.pk]))
        self.assertEqual(r.status_code, 302)
        resa.refresh_from_db()
        self.assertEqual(resa.statut, "confirmee")
        self.assertTrue(resa.lien_visio.startswith("https://meet.jit.si/"))


class DispoCrudTests(TestCase):
    """CRUD Disponibilite : mentor proprietaire OK, autre mentor 404, apprenant 403."""

    def setUp(self):
        self.mentor = User.objects.create_user(username="m2", password="x", email="m2@ex.tn", role="mentor")
        self.mentor2 = User.objects.create_user(username="m3", password="x", email="m3@ex.tn", role="mentor")
        self.app = User.objects.create_user(username="a2", password="x", email="a2@ex.tn")
        self.profil = MentorProfile.objects.get_or_create(mentor=self.mentor, defaults={"verifie": True})[0]
        debut = timezone.now() + timedelta(days=2)
        self.dispo = Disponibilite.objects.create(
            mentor=self.profil, debut=debut, fin=debut + timedelta(hours=1))

    def test_dispo_update_proprietaire(self):
        self.client.force_login(self.mentor)
        debut = timezone.now() + timedelta(days=3)
        fin = debut + timedelta(hours=1)
        r = self.client.post(reverse("mentoring:dispo-update", args=[self.dispo.pk]), {
            "debut": debut.strftime("%Y-%m-%dT%H:%M"), "fin": fin.strftime("%Y-%m-%dT%H:%M")})
        self.assertEqual(r.status_code, 302)

    def test_dispo_update_autre_mentor_404(self):
        self.client.force_login(self.mentor2)
        r = self.client.get(reverse("mentoring:dispo-update", args=[self.dispo.pk]))
        self.assertEqual(r.status_code, 404)

    def test_dispo_update_apprenant_403(self):
        self.client.force_login(self.app)
        r = self.client.get(reverse("mentoring:dispo-update", args=[self.dispo.pk]))
        self.assertEqual(r.status_code, 403)

    def test_dispo_passee_refusee(self):
        self.client.force_login(self.mentor)
        passe = timezone.now() - timedelta(days=1)
        r = self.client.post(reverse("mentoring:dispo-create"), {
            "debut": passe.strftime("%Y-%m-%dT%H:%M"),
            "fin": (passe + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")})
        self.assertEqual(r.status_code, 200)  # formulaire reinvalide, pas de creation
        self.assertIn("futur", r.context["form"].errors.as_text())

    def test_api_dispo_detail_put_proprietaire(self):
        self.assertEqual(
            self.client.get(reverse("mentoring-api:detail-disponibilite", args=[self.dispo.pk])).status_code, 200)
        self.client.force_login(self.mentor)
        debut = timezone.now() + timedelta(days=5)
        r = self.client.put(
            reverse("mentoring-api:detail-disponibilite", args=[self.dispo.pk]),
            {"debut": debut.isoformat(), "fin": (debut + timedelta(hours=1)).isoformat()},
            content_type="application/json")
        self.assertEqual(r.status_code, 200)
