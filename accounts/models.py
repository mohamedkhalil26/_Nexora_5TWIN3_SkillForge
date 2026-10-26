"""Modeles accounts — Ch4 : User personnalise DES LE DEBUT + Ch2 Meta/validateurs."""
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.urls import reverse

from common.validators import validate_image_size

ROLES = (
    ("apprenant", "Apprenant"),
    ("mentor", "Mentor"),
    ("admin", "Administrateur"),
)

NIVEAUX = (
    ("debutant", "Débutant"),
    ("intermediaire", "Intermédiaire"),
    ("avance", "Avancé"),
)


class Utilisateur(AbstractUser):
    """Utilisateur custom : email identifiant + role SkillForge (Ch4 AbstractUser)."""

    email = models.EmailField("E-mail", unique=True)
    role = models.CharField("Rôle", max_length=20, choices=ROLES, default="apprenant")
    telephone = models.CharField(
        "Téléphone",
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\+?[0-9\s\-\.]{6,20}$", "Numéro invalide.")],
    )
    niveau = models.CharField("Niveau", max_length=20, choices=NIVEAUX, default="debutant")
    objectifs = models.TextField("Objectifs d'apprentissage", blank=True, max_length=1000)
    bio = models.TextField("Biographie", blank=True, max_length=1000)
    avatar = models.ImageField(
        "Avatar",
        upload_to="avatars/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_absolute_url(self):
        return reverse("accounts:profil", args=[self.pk])

    @property
    def est_apprenant(self):
        return self.role == "apprenant"

    @property
    def est_mentor(self):
        return self.role == "mentor"

    @property
    def est_admin(self):
        return self.role == "admin" or self.is_superuser
