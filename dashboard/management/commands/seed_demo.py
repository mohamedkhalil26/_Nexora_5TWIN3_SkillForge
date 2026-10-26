"""Seed de demo — Ch3 : groupes metier + permissions + jeu de donnees soutenance.

Usage : python manage.py seed_demo
Comptes crees (mot de passe : demo1234) : admin / mentor1 / mentor2 / apprenant1 / apprenant2
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Cree groupes, utilisateurs demo et jeu de donnees SkillForge."

    def handle(self, *args, **options):
        from certification.models import Certificat
        from certification.pdf import generer_certificat_pdf
        from learning.models import Competence, Cours, Module, Ressource
        from mentoring.models import Disponibilite, MentorProfile, Message, Reservation
        from quizzes.models import Question, Quiz, Reponse, Tentative

        # ---- Groupes metier (Ch3 : permissions plutot que superuser) ----
        mentors_group, _ = Group.objects.get_or_create(name="Mentors")
        gestionnaires, _ = Group.objects.get_or_create(name="Gestionnaires Catalogue")
        perms_cours = Permission.objects.filter(
            content_type__app_label="learning", content_type__model="cours"
        )
        gestionnaires.permissions.set(perms_cours)
        self.stdout.write(self.style.SUCCESS("Groupes OK."))

        # ---- Utilisateurs demo ----
        def get_or_create_user(username, role, **kwargs):
            user, created = User.objects.get_or_create(username=username, defaults=kwargs)
            if created:
                user.set_password("demo1234")
                user.role = role
                user.save()
            return user

        admin = get_or_create_user(
            "admin", "admin", email="admin@skillforge.tn", is_staff=True, is_superuser=True
        )
        mentor1 = get_or_create_user("mentor1", "mentor", email="mentor1@skillforge.tn")
        mentor2 = get_or_create_user(
            "mentor2",
            "mentor",
            email="mentor2@skillforge.tn",
            niveau="avance",
            objectifs="Transmettre mon expérience Python aux débutants",
        )
        apprenant1 = get_or_create_user(
            "apprenant1",
            "apprenant",
            email="apprenant1@skillforge.tn",
            objectifs="Je veux créer un site web avec Django",
            niveau="debutant",
        )
        apprenant2 = get_or_create_user(
            "apprenant2",
            "apprenant",
            email="apprenant2@skillforge.tn",
            objectifs="Je veux maîtriser Python pour l'analyse de données",
            niveau="intermediaire",
        )
        mentor1.groups.add(mentors_group)
        mentor2.groups.add(mentors_group)
        self.stdout.write(self.style.SUCCESS("Utilisateurs OK (mdp : demo1234)."))

        # ---- Competences ----
        python, _ = Competence.objects.get_or_create(
            slug="python",
            defaults={
                "nom": "Python",
                "description": "Le langage de programmation Python, des bases aux projets : syntaxe, fonctions, POO, bibliothèques data.",
            },
        )
        django_skill, _ = Competence.objects.get_or_create(
            slug="django",
            defaults={
                "nom": "Django",
                "description": "Créer des sites web complets avec le framework Django : modèles, vues, templates.",
            },
        )
        data_skill, _ = Competence.objects.get_or_create(
            slug="data-analyse",
            defaults={
                "nom": "Analyse de données",
                "description": "Nettoyer, explorer et visualiser des données avec Python : pandas, matplotlib, statistiques descriptives.",
            },
        )

        # ---- Cours ----
        cours_django, _ = Cours.objects.get_or_create(
            slug="django-debutant",
            defaults={
                "competence": django_skill,
                "titre": "Django pour débutants",
                "description": "Apprenez à créer votre premier site web avec Django : modèles, vues, templates et admin.",
                "auteur": admin,
                "duree_minutes": 180,
                "publie": True,
            },
        )
        cours_python, _ = Cours.objects.get_or_create(
            slug="python-fondamentaux",
            defaults={
                "competence": python,
                "titre": "Python — fondamentaux",
                "description": "Variables, boucles, fonctions et POO : les bases solides pour tout projet Python.",
                "auteur": admin,
                "duree_minutes": 240,
                "publie": True,
            },
        )
        cours_data, _ = Cours.objects.get_or_create(
            slug="data-pandas",
            defaults={
                "competence": data_skill,
                "titre": "Analyser des données avec pandas",
                "description": "Chargez un CSV, nettoyez-le et produisez vos premiers graphiques avec pandas et matplotlib.",
                "auteur": admin,
                "duree_minutes": 200,
                "publie": True,
            },
        )

        # ---- Modules ----
        m_dj1, _ = Module.objects.get_or_create(
            cours=cours_django,
            ordre=1,
            defaults={
                "titre": "Introduction à Django",
                "contenu": (
                    "Django est un framework web Python. Il suit le patron "
                    "Modèle-Vue-Template. Le modèle gère les données via l'ORM. "
                    "La vue contient la logique métier. Le template affiche le HTML. "
                    "L'admin permet de gérer les données sans coder."
                ),
            },
        )
        Module.objects.get_or_create(
            cours=cours_django,
            ordre=2,
            defaults={
                "titre": "Vues et templates",
                "contenu": (
                    "Une vue reçoit la requête HTTP et renvoie une réponse. "
                    "Le template affiche les données avec le langage DTL : variables, "
                    "filtres, boucles et héritage via base.html. "
                    "Les URLs relient chaque adresse à sa vue avec des routes nommées."
                ),
            },
        )
        m_py1, _ = Module.objects.get_or_create(
            cours=cours_python,
            ordre=1,
            defaults={
                "titre": "Bases Python",
                "contenu": (
                    "Python est un langage simple et lisible. Les variables ne se déclarent pas. "
                    "Les boucles for et while répètent des actions. Les fonctions réutilisent "
                    "du code. Les listes et dictionnaires structurent les données."
                ),
            },
        )
        Ressource.objects.get_or_create(
            module=m_py1,
            titre="Documentation officielle Python",
            defaults={"type": "lien", "url": "https://docs.python.org/fr/3/tutorial/"},
        )
        Ressource.objects.get_or_create(
            module=m_dj1,
            titre="Documentation Django",
            defaults={"type": "lien", "url": "https://docs.djangoproject.com/fr/5.2/"},
        )

        # ---- Quiz demo ----
        quiz_dj, _ = Quiz.objects.get_or_create(
            cours=cours_django,
            titre="Quiz Django — bases",
            defaults={"seuil_reussite": 70, "actif": True},
        )
        if quiz_dj.questions.count() == 0:
            Question.objects.create(
                quiz=quiz_dj,
                type="qcm",
                ordre=1,
                enonce="Quel composant Django gère l'accès base de données ?",
                choix="Le template\nLe modèle (ORM)\nLe fichier CSS",
                bonne_reponse="2",
                points=1,
            )
            Question.objects.create(
                quiz=quiz_dj,
                type="libre",
                ordre=2,
                enonce="Expliquez le rôle d'une vue Django en deux phrases.",
                bonne_reponse="La vue reçoit la requête, applique la logique métier et renvoie une réponse HTML via un template.",
                points=2,
            )
        quiz_py, _ = Quiz.objects.get_or_create(
            cours=cours_python,
            titre="Quiz Python — fondamentaux",
            defaults={"seuil_reussite": 60, "actif": True},
        )
        if quiz_py.questions.count() == 0:
            Question.objects.create(
                quiz=quiz_py,
                type="qcm",
                ordre=1,
                enonce="Quelle structure stocke des paires clé-valeur en Python ?",
                choix="La liste\nLe tuple\nLe dictionnaire",
                bonne_reponse="3",
                points=1,
            )
            Question.objects.create(
                quiz=quiz_py,
                type="libre",
                ordre=2,
                enonce="Citez deux avantages d'écrire une fonction plutôt que du code répété.",
                bonne_reponse="Une fonction évite la répétition et rend le code réutilisable et plus facile à tester.",
                points=2,
            )

        # ---- Mentors demo ----
        profil1, _ = MentorProfile.objects.get_or_create(
            mentor=mentor1,
            defaults={"presentation": "Développeur Django, j'accompagne les débutants.", "verifie": True},
        )
        profil1.specialites.add(django_skill, python)
        profil2, _ = MentorProfile.objects.get_or_create(
            mentor=mentor2,
            defaults={"presentation": "Data analyst, je rends pandas simple et concret.", "verifie": True},
        )
        profil2.specialites.add(python, data_skill)
        for profil in (profil1, profil2):
            if profil.disponibilites.count() == 0:
                debut = timezone.now().replace(hour=14, minute=0, second=0, microsecond=0)
                for j in (1, 3, 5):
                    d = debut + timedelta(days=j)
                    Disponibilite.objects.create(mentor=profil, debut=d, fin=d + timedelta(hours=1))

        # ---- Tentative reussie demo (apprenant1 : 2/2 au quiz Django) ----
        if not Tentative.objects.filter(apprenant=apprenant1, quiz=quiz_dj).exists():
            t = Tentative.objects.create(quiz=quiz_dj, apprenant=apprenant1, score=100.0, reussi=True)
            for q in quiz_dj.questions.all():
                Reponse.objects.create(
                    tentative=t, question=q, reponse_donnee=q.bonne_reponse,
                    correct=True, points_obtenus=float(q.points),
                )
            t.feedback = "Excellent travail, visez la certification Django."
            t.save(update_fields=["feedback"])

        # ---- Reservation confirmee demo + message ----
        dispo = profil1.disponibilites.filter(reserve=False).first()
        if dispo and not Reservation.objects.filter(apprenant=apprenant1).exists():
            resa = Reservation.objects.create(
                disponibilite=dispo,
                apprenant=apprenant1,
                statut="confirmee",
                sujet="Revue de mon premier projet Django",
            )
            resa.generer_lien_visio()
            resa.save(update_fields=["lien_visio"])
            dispo.reserve = True
            dispo.save(update_fields=["reserve"])
            Message.objects.create(
                reservation=resa, auteur=mentor1,
                contenu="Bonjour ! Préparez 2-3 questions sur les vues, on les traitera en session.",
            )

        # ---- Certificat Python demo pour apprenant2 ----
        if not Certificat.objects.filter(apprenant=apprenant2, competence=python).exists():
            cert = Certificat.objects.create(
                apprenant=apprenant2, competence=python, score_final=85.0, delivre_par=admin
            )
            cert.fichier.save(f"certificat-{cert.code}.pdf", ContentFile(generer_certificat_pdf(cert)))

        self.stdout.write(self.style.SUCCESS("Seed termine. Lancez : python manage.py runserver"))
