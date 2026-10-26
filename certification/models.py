"""Modeles certification — Malek : certificats + generation PDF."""
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse


class Certificat(models.Model):
    apprenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificats",
        verbose_name="Apprenant",
    )
    competence = models.ForeignKey(
        "learning.Competence",
        on_delete=models.PROTECT,  # Ch2 : le certificat survit a la competence
        related_name="certificats",
        verbose_name="Compétence",
    )
    code = models.UUIDField("Code unique", default=uuid.uuid4, unique=True, editable=False)
    score_final = models.FloatField(
        "Score final (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    fichier = models.FileField("PDF", upload_to="certificats/", blank=True, null=True)
    delivre_le = models.DateTimeField("Délivré le", auto_now_add=True)
    delivre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificats_delivres",
        verbose_name="Délivré par",
    )

    class Meta:
        verbose_name = "Certificat"
        verbose_name_plural = "Certificats"
        ordering = ["-delivre_le"]
        constraints = [
            models.UniqueConstraint(
                fields=["apprenant", "competence"], name="unique_certificat_par_competence"
            )
        ]

    def __str__(self):
        return f"{self.apprenant.username} — {self.competence.nom} ({self.score_final:.0f}%)"

    def get_absolute_url(self):
        return reverse("certification:certificat-detail", args=[self.pk])


def est_eligible(apprenant, competence, seuil: float = 70.0) -> tuple[bool, float]:
    """Eligible si moyenne des tentatives sur la competence >= seuil."""
    from quizzes.models import Tentative

    tentatives = Tentative.objects.filter(
        apprenant=apprenant, quiz__cours__competence=competence
    )
    if not tentatives.exists():
        return False, 0.0
    # meilleur score par quiz
    par_quiz: dict[int, float] = {}
    for t in tentatives:
        qid = t.quiz_id
        par_quiz[qid] = max(par_quiz.get(qid, 0), t.score)
    moyenne = sum(par_quiz.values()) / len(par_quiz)
    return moyenne >= seuil, round(moyenne, 1)
