"""Tests quizzes — Tache prio #1 : correction QCM/libre, passation, API soumission."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from learning.models import Competence, Cours

from .ai import corriger_libre, corriger_qcm, predire_risque
from .models import Question, Quiz, Tentative

User = get_user_model()


class CorrectionTests(TestCase):
    def test_qcm(self):
        q = Question(type="qcm", enonce="?", bonne_reponse="2", points=2)
        ok, pts = corriger_qcm(q, "2")
        self.assertEqual((ok, pts), (True, 2.0))
        ok, pts = corriger_qcm(q, "1")
        self.assertEqual((ok, pts), (False, 0.0))

    def test_libre_fallback_identique(self):
        q = Question(type="libre", enonce="?", bonne_reponse="la vue renvoie du html", points=2)
        ok, pts, fb = corriger_libre(q, "la vue renvoie du html")
        self.assertTrue(ok and pts > 0 and fb)

    def test_libre_vide(self):
        q = Question(type="libre", enonce="?", bonne_reponse="x", points=1)
        ok, pts, fb = corriger_libre(q, "   ")
        self.assertFalse(ok)
        self.assertEqual(pts, 0.0)

    def test_risque(self):
        self.assertEqual(predire_risque([90, 92]), "excellent")
        self.assertEqual(predire_risque([20, 30]), "a_risque")


class PassationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        comp = Competence.objects.create(nom="C", description="d", slug="c")
        cours = Cours.objects.create(competence=comp, titre="T", slug="t", description="d", publie=True)
        self.quiz = Quiz.objects.create(cours=cours, titre="Q", seuil_reussite=50)
        self.q = Question.objects.create(
            quiz=self.quiz, type="qcm", ordre=1, enonce="?",
            choix="A\nB", bonne_reponse="1", points=1,
        )

    def test_passer_quiz_enregistre_tentative(self):
        self.client.force_login(self.user)
        r = self.client.post(
            reverse("quizzes:quiz-passer", args=[self.quiz.pk]), {f"q_{self.q.pk}": "1"}
        )
        self.assertEqual(r.status_code, 302)
        t = Tentative.objects.get(apprenant=self.user)
        self.assertTrue(t.reussi and t.score == 100.0)

    def test_api_soumettre(self):
        self.client.force_login(self.user)
        r = self.client.post(
            reverse("quizzes-api:soumettre-quiz", args=[self.quiz.pk]),
            {"reponses": {str(self.q.pk): "1"}},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.json()["reussi"])


class QuizCrudTests(TestCase):
    """CRUD Quiz/Question : mentor OK, apprenant 403 ; anti-fraude copie."""

    def setUp(self):
        self.mentor = User.objects.create_user(username="m", password="x", email="m@ex.tn", role="mentor")
        self.app = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        comp = Competence.objects.create(nom="C", description="d", slug="c2")
        self.cours = Cours.objects.create(competence=comp, titre="T", slug="t2", description="d", publie=True)
        self.quiz = Quiz.objects.create(cours=self.cours, titre="Q", seuil_reussite=50)
        self.q = Question.objects.create(
            quiz=self.quiz, type="libre", ordre=1, enonce="Expliquez les vues",
            bonne_reponse="la vue renvoie du html", points=2)

    def test_quiz_update_mentor(self):
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("quizzes:quiz-update", args=[self.quiz.pk]), {
            "cours": self.cours.pk, "titre": "Q2", "seuil_reussite": 60, "actif": True})
        self.assertEqual(r.status_code, 302)
        self.quiz.refresh_from_db()
        self.assertEqual(self.quiz.titre, "Q2")

    def test_quiz_delete_apprenant_403(self):
        self.client.force_login(self.app)
        r = self.client.get(reverse("quizzes:quiz-delete", args=[self.quiz.pk]))
        self.assertEqual(r.status_code, 403)

    def test_question_list_connecte(self):
        self.client.force_login(self.app)
        r = self.client.get(reverse("quizzes:question-list", args=[self.quiz.pk]))
        self.assertEqual(r.status_code, 200)

    def test_antifraude_copie_zero(self):
        # Un autre apprenant a deja donne la meme reponse libre.
        autre = User.objects.create_user(username="b", password="x", email="b@ex.tn")
        t0 = Tentative.objects.create(quiz=self.quiz, apprenant=autre, score=100.0)
        from .models import Reponse as Rep
        Rep.objects.create(tentative=t0, question=self.q,
            reponse_donnee="la vue renvoie du html", correct=True, points_obtenus=2.0)
        self.client.force_login(self.app)
        r = self.client.post(
            reverse("quizzes:quiz-passer", args=[self.quiz.pk]),
            {f"q_{self.q.pk}": "la vue renvoie du html"})
        self.assertEqual(r.status_code, 302)
        t = Tentative.objects.filter(apprenant=self.app).latest("date")
        self.assertEqual(t.score, 0.0)  # copie detectee

    def test_api_questions_public_et_post_mentor(self):
        self.assertEqual(self.client.get(reverse("quizzes-api:questions")).status_code, 200)
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("quizzes-api:questions"),
            {"quiz": self.quiz.pk, "type": "qcm", "ordre": 2,
             "enonce": "?", "choix": "A\nB", "bonne_reponse": "1", "points": 1},
            content_type="application/json")
        self.assertEqual(r.status_code, 201)
