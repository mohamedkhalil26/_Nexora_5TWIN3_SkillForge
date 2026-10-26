"""Modeles mentoring — Raed : profils mentors, disponibilites, reservations, messages."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse

STATUTS_RESERVATION = (
    ("en_attente", "En attente"),
    ("confirmee", "Confirmée"),
    ("annulee", "Annulée"),
    ("terminee", "Terminée"),
)


class MentorProfile(models.Model):
    mentor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profil_mentor",
        verbose_name="Mentor",
    )
    specialites = models.ManyToManyField(
        "learning.Competence", related_name="mentors", verbose_name="Spécialités", blank=True
    )
    presentation = models.TextField("Présentation", max_length=2000, blank=True)
    tarif = models.DecimalField(
        "Tarif / session (DT)",
        max_digits=8,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
    )
    verifie = models.BooleanField("Vérifié par l'admin", default=False)

    class Meta:
        verbose_name = "Profil mentor"
        verbose_name_plural = "Profils mentors"
        ordering = ["mentor__username"]

    def __str__(self):
        return f"Mentor {self.mentor.username}"

    def get_absolute_url(self):
        return reverse("mentoring:mentor-detail", args=[self.pk])


class Disponibilite(models.Model):
    mentor = models.ForeignKey(
        MentorProfile,
        on_delete=models.CASCADE,
        related_name="disponibilites",
        verbose_name="Mentor",
    )
    debut = models.DateTimeField("Début")
    fin = models.DateTimeField("Fin")
    reserve = models.BooleanField("Réservée", default=False)

    class Meta:
        verbose_name = "Disponibilité"
        verbose_name_plural = "Disponibilités"
        ordering = ["debut"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fin__gt=models.F("debut")), name="fin_apres_debut"
            )
        ]

    def __str__(self):
        return f"{self.mentor.mentor.username} : {self.debut:%d/%m %H:%M} → {self.fin:%H:%M}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        if self.debut and self.fin and self.fin <= self.debut:
            raise ValidationError("La fin doit être après le début.")
        if self.debut and self.debut < timezone.now():
            raise ValidationError("Le créneau doit être dans le futur.")


class Reservation(models.Model):
    disponibilite = models.OneToOneField(
        Disponibilite,
        on_delete=models.PROTECT,  # Ch2 : PROTECT, on ne perd jamais l'historique
        related_name="reservation",
        verbose_name="Créneau",
    )
    apprenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Apprenant",
    )
    statut = models.CharField(
        "Statut", max_length=20, choices=STATUTS_RESERVATION, default="en_attente"
    )
    sujet = models.CharField("Sujet de la session", max_length=300)
    lien_visio = models.URLField("Lien visio (Jitsi)", blank=True)
    cree_le = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.apprenant.username} ↔ {self.disponibilite} [{self.get_statut_display()}]"

    def get_absolute_url(self):
        return reverse("mentoring:reservation-detail", args=[self.pk])

    @property
    def mentor(self):
        return self.disponibilite.mentor.mentor

    def generer_lien_visio(self):
        if not self.lien_visio:
            self.lien_visio = f"https://meet.jit.si/skillforge-{self.pk}"
        return self.lien_visio


class Message(models.Model):
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Réservation",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Auteur"
    )
    contenu = models.TextField("Message", max_length=2000)
    date = models.DateTimeField("Date", auto_now_add=True)
    lu = models.BooleanField("Lu", default=False)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ["date"]

    def __str__(self):
        return f"{self.auteur.username} ({self.date:%d/%m %H:%M})"
