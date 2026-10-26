"""Modeles quizzes — Mariem : Quiz -> Question (QCM + libre) -> Tentative."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

TYPES_QUESTION = (
    ("qcm", "QCM"),
    ("libre", "Réponse libre"),
)


class Quiz(models.Model):
    cours = models.ForeignKey(
        "learning.Cours", on_delete=models.CASCADE, related_name="quiz", verbose_name="Cours"
    )
    titre = models.CharField("Titre", max_length=200)
    seuil_reussite = models.PositiveIntegerField(
        "Seuil de réussite (%)",
        default=70,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    actif = models.BooleanField("Actif", default=True)
    cree_le = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.titre} ({self.cours.titre})"

    def get_absolute_url(self):
        return reverse("quizzes:quiz-detail", args=[self.pk])


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="Quiz"
    )
    type = models.CharField("Type", max_length=10, choices=TYPES_QUESTION, default="qcm")
    enonce = models.TextField("Énoncé", max_length=2000)
    # QCM : choix separes par des lignes, bonne reponse = index (1-based)
    choix = models.TextField("Choix (un par ligne, QCM)", blank=True, max_length=2000)
    bonne_reponse = models.TextField(
        "Bonne réponse : n° du choix (QCM) ou réponse attendue (libre)",
        max_length=2000,
    )
    points = models.PositiveIntegerField("Points", default=1, validators=[MinValueValidator(1)])
    ordre = models.PositiveIntegerField("Ordre", default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["quiz", "ordre"]
        constraints = [
            models.UniqueConstraint(fields=["quiz", "ordre"], name="unique_ordre_question")
        ]

    def __str__(self):
        return f"Q{self.ordre} — {self.enonce[:60]}"

    def liste_choix(self) -> list[str]:
        return [c.strip() for c in (self.choix or "").splitlines() if c.strip()]


class Tentative(models.Model):
    """Une passation de quiz par un apprenant (meilleur score conserve via logique)."""

    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="tentatives", verbose_name="Quiz"
    )
    apprenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tentatives",
        verbose_name="Apprenant",
    )
    score = models.FloatField(
        "Score (%)",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    reussi = models.BooleanField("Réussi", default=False)
    feedback = models.TextField("Feedback IA", blank=True, max_length=5000)
    date = models.DateTimeField("Date", auto_now_add=True)

    class Meta:
        verbose_name = "Tentative"
        verbose_name_plural = "Tentatives"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.apprenant.username} — {self.quiz.titre} : {self.score:.0f}%"

    def get_absolute_url(self):
        return reverse("quizzes:tentative-detail", args=[self.pk])


class Reponse(models.Model):
    tentative = models.ForeignKey(
        Tentative, on_delete=models.CASCADE, related_name="reponses", verbose_name="Tentative"
    )
    question = models.ForeignKey(
        Question, on_delete=models.PROTECT, related_name="reponses", verbose_name="Question"
    )
    reponse_donnee = models.TextField("Réponse donnée", max_length=5000)
    correct = models.BooleanField("Correcte", default=False)
    points_obtenus = models.FloatField("Points obtenus", default=0)

    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        constraints = [
            models.UniqueConstraint(
                fields=["tentative", "question"], name="unique_reponse_par_tentative"
            )
        ]

    def __str__(self):
        return f"{self.tentative} / Q{self.question.ordre}"
