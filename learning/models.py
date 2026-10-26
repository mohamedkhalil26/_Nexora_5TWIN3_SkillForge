"""Modeles learning — Mahdi : hierarchie Competence -> Cours -> Module -> Ressource."""
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse

from common.validators import validate_file_size, validate_image_size

TYPES_RESSOURCE = (
    ("texte", "Texte"),
    ("video", "Vidéo (URL)"),
    ("pdf", "Document PDF"),
    ("lien", "Lien externe"),
)


class Competence(models.Model):
    nom = models.CharField("Nom", max_length=120, unique=True)
    description = models.TextField("Description", max_length=2000)
    slug = models.SlugField("Slug", max_length=140, unique=True)
    image = models.ImageField(
        "Illustration",
        upload_to="covers/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
    )

    class Meta:
        verbose_name = "Compétence"
        verbose_name_plural = "Compétences"
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("learning:competence-detail", args=[self.slug])


class Cours(models.Model):
    competence = models.ForeignKey(
        Competence, on_delete=models.CASCADE, related_name="cours", verbose_name="Compétence"
    )
    titre = models.CharField("Titre", max_length=200)
    description = models.TextField("Description", max_length=3000)
    slug = models.SlugField("Slug", max_length=220, unique=True)
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cours_crees",
        verbose_name="Auteur",
    )
    duree_minutes = models.PositiveIntegerField(
        "Durée estimée (min)", default=60, validators=[MinValueValidator(1)]
    )
    publie = models.BooleanField("Publié", default=False)
    cree_le = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ["-cree_le"]
        constraints = [
            models.UniqueConstraint(fields=["competence", "titre"], name="unique_cours_par_competence")
        ]

    def __str__(self):
        return self.titre

    def get_absolute_url(self):
        return reverse("learning:cours-detail", args=[self.slug])


class Module(models.Model):
    cours = models.ForeignKey(
        Cours, on_delete=models.CASCADE, related_name="modules", verbose_name="Cours"
    )
    titre = models.CharField("Titre", max_length=200)
    contenu = models.TextField("Contenu", max_length=20000)
    ordre = models.PositiveIntegerField("Ordre", default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ["cours", "ordre"]
        constraints = [
            models.UniqueConstraint(fields=["cours", "ordre"], name="unique_ordre_module")
        ]

    def __str__(self):
        return f"{self.cours.titre} — {self.titre}"

    def get_absolute_url(self):
        return reverse("learning:module-detail", args=[self.pk])


class Ressource(models.Model):
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="ressources", verbose_name="Module"
    )
    titre = models.CharField("Titre", max_length=200)
    type = models.CharField("Type", max_length=10, choices=TYPES_RESSOURCE, default="lien")
    url = models.URLField("URL", blank=True)
    fichier = models.FileField(
        "Fichier",
        upload_to="ressources/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "mp4", "zip", "txt", "md"]),
            validate_file_size,
        ],
    )

    class Meta:
        verbose_name = "Ressource"
        verbose_name_plural = "Ressources"
        ordering = ["module", "titre"]

    def __str__(self):
        return f"{self.titre} ({self.get_type_display()})"
