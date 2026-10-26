"""Validateurs fichiers — Tache prio #4 : whitelist extensions + limite de taille."""
from django.core.exceptions import ValidationError


def validate_image_size(value, max_mb=5):
    """Refuse les images > max_mb Mo (avatars, covers)."""
    if value and value.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Fichier trop volumineux (max {max_mb} Mo).")


def validate_file_size(value, max_mb=10):
    """Refuse les fichiers > max_mb Mo (ressources PDF...)."""
    if value and value.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Fichier trop volumineux (max {max_mb} Mo).")
