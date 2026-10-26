"""Tests certification — Tache prio #1 : eligibilite, demande, PDF."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from learning.models import Competence, Cours
from quizzes.models import Question, Quiz, Reponse, Tentative

from .ai import detecter_similarite, predire_reussite
from .models import Certificat, est_eligible

User = get_user_model()


class CertificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        self.comp = Competence.objects.create(nom="Django", description="web", slug="dj")
        self.cours = Cours.objects.create(
            competence=self.comp, titre="T", slug="t", description="d", publie=True
        )
        self.quiz = Quiz.objects.create(cours=self.cours, titre="Q", seuil_reussite=70)

    def _tentative(self, score):
        t = Tentative.objects.create(quiz=self.quiz, apprenant=self.user, score=score)
        return t

    def test_non_eligible_sans_tentative(self):
        eligible, moyenne = est_eligible(self.user, self.comp)
        self.assertFalse(eligible)
        self.assertEqual(moyenne, 0.0)

    def test_eligible_bon_score(self):
        self._tentative(85.0)
        eligible, moyenne = est_eligible(self.user, self.comp)
        self.assertTrue(eligible)
        self.assertEqual(moyenne, 85.0)

    def test_demande_delivre_et_unicite(self):
        self._tentative(90.0)
        self.client.force_login(self.user)
        r = self.client.post(reverse("certification:certificat-demander", args=["dj"]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Certificat.objects.filter(apprenant=self.user).count(), 1)
        r = self.client.post(reverse("certification:certificat-demander", args=["dj"]))
        self.assertEqual(Certificat.objects.filter(apprenant=self.user).count(), 1)  # pas de doublon

    def test_demande_refusee_sous_seuil(self):
        self._tentative(40.0)
        self.client.force_login(self.user)
        r = self.client.post(reverse("certification:certificat-demander", args=["dj"]))
        self.assertEqual(Certificat.objects.count(), 0)

    def test_prediction_et_antifraude(self):
        proba, msg = predire_reussite([80, 85])
        self.assertGreaterEqual(proba, 70)
        self.assertTrue(msg)
        self.assertTrue(detecter_similarite("la vue renvoie du html", ["la vue renvoie du html"]))
        self.assertFalse(detecter_similarite("les templates affichent", ["la base de donnees"]))
