"""Tests accounts — Tache prio #1 : inscription, profil, permissions, IA fallback."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from learning.models import Competence

from .ai import recommander_competences, suggerer_bio

User = get_user_model()


class InscriptionTests(TestCase):
    def test_register_cree_apprenant(self):
        r = self.client.post(
            reverse("accounts:register"),
            {
                "username": "nouveau",
                "email": "nouveau@ex.tn",
                "role": "apprenant",
                "niveau": "debutant",
                "objectifs": "apprendre Django",
                "password1": "MotDePasseFort123!",
                "password2": "MotDePasseFort123!",
            },
        )
        self.assertEqual(r.status_code, 302)  # PRG vers login
        user = User.objects.get(username="nouveau")
        self.assertEqual(user.role, "apprenant")

    def test_profil_prive_redirige_anonyme(self):
        user = User.objects.create_user(username="u1", password="x", email="u1@ex.tn")
        r = self.client.get(reverse("accounts:profil", args=[user.pk]))
        self.assertEqual(r.status_code, 302)  # vers login

    def test_profil_autre_utilisateur_interdit(self):
        u1 = User.objects.create_user(username="u1", password="x", email="u1@ex.tn")
        u2 = User.objects.create_user(username="u2", password="x", email="u2@ex.tn")
        self.client.force_login(u2)
        r = self.client.get(reverse("accounts:profil", args=[u1.pk]))
        self.assertEqual(r.status_code, 403)


class AiAccountsTests(TestCase):
    def test_recommandations_sans_cle(self):
        Compete = Competence
        c = Compete.objects.create(
            nom="Django", description="framework web python", slug="dj-test"
        )
        recos = recommander_competences("je veux créer un site web", [c])
        self.assertEqual(recos, [c])

    def test_bio_fallback(self):
        bio = suggerer_bio("apprendre Django", "debutant")
        self.assertIn("debutant", bio)
