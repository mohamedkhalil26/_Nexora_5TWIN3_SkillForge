"""Tests learning — Tache prio #1 : CRUD staff-only, recherche IA, resume/tags."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .ai import auto_tags, recherche_semantique, resumer_module
from .models import Competence, Cours, Module

User = get_user_model()


class CoursTests(TestCase):
    def setUp(self):
        self.comp = Competence.objects.create(nom="Django", description="web", slug="dj")
        self.cours = Cours.objects.create(
            competence=self.comp, titre="Django 101", slug="dj-101",
            description="cours test", publie=True,
        )

    def test_liste_publique_ok(self):
        self.assertEqual(self.client.get(reverse("learning:cours-list")).status_code, 200)

    def test_creation_reservee_staff(self):
        r = self.client.get(reverse("learning:cours-create"))
        self.assertEqual(r.status_code, 302)  # login requis
        user = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        self.client.force_login(user)
        r = self.client.get(reverse("learning:cours-create"))
        self.assertEqual(r.status_code, 403)  # apprenant refuse

    def test_recherche_semantique(self):
        res = recherche_semantique("créer un site", [self.cours])
        self.assertIn(self.cours, res)

    def test_resume_et_tags(self):
        module = Module.objects.create(
            cours=self.cours, titre="M1", ordre=1,
            contenu=("Django est un framework. " * 5) + ("Le template affiche le HTML. " * 5),
        )
        self.assertTrue(len(resumer_module(module.contenu)) < len(module.contenu))
        self.assertTrue(len(auto_tags(module.titre, module.contenu)) > 0)


class CompetenceCrudTests(TestCase):
    """CRUD Competence + Module delete + Ressource : mentor OK, apprenant 403."""

    def setUp(self):
        self.mentor = User.objects.create_user(username="m", password="x", email="m@ex.tn", role="mentor")
        self.app = User.objects.create_user(username="a", password="x", email="a@ex.tn")
        self.comp = Competence.objects.create(nom="Django", description="web", slug="dj")
        self.cours = Cours.objects.create(
            competence=self.comp, titre="T", slug="t", description="d", publie=True
        )
        self.module = Module.objects.create(cours=self.cours, titre="M1", ordre=1, contenu="x" * 30)

    def test_competence_create_mentor(self):
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("learning:competence-create"), {
            "nom": "Python", "description": "langage", "slug": "python"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Competence.objects.filter(slug="python").exists())

    def test_competence_create_apprenant_403(self):
        self.client.force_login(self.app)
        r = self.client.get(reverse("learning:competence-create"))
        self.assertEqual(r.status_code, 403)

    def test_competence_delete_mentor(self):
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("learning:competence-delete", args=["dj"]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Competence.objects.filter(slug="dj").exists())

    def test_module_delete_mentor(self):
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("learning:module-delete", args=[self.module.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Module.objects.filter(pk=self.module.pk).exists())

    def test_module_delete_apprenant_403(self):
        self.client.force_login(self.app)
        r = self.client.get(reverse("learning:module-delete", args=[self.module.pk]))
        self.assertEqual(r.status_code, 403)

    def test_ressource_create_mentor(self):
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("learning:ressource-create"), {
            "module": self.module.pk, "titre": "Doc", "type": "lien",
            "url": "https://example.com"})
        self.assertEqual(r.status_code, 302)

    def test_api_modules_public_et_post_mentor(self):
        self.assertEqual(self.client.get(reverse("learning-api:modules")).status_code, 200)
        r = self.client.post(reverse("learning-api:modules"),
            {"cours": self.cours.pk, "titre": "M2", "contenu": "y" * 30, "ordre": 2},
            content_type="application/json")
        self.assertEqual(r.status_code, 403)  # anonyme refuse
        self.client.force_login(self.mentor)
        r = self.client.post(reverse("learning-api:modules"),
            {"cours": self.cours.pk, "titre": "M2", "contenu": "y" * 30, "ordre": 2},
            content_type="application/json")
        self.assertEqual(r.status_code, 201)
