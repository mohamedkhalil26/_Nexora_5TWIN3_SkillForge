"""Formulaires accounts — Ch6 : ModelForm + UserCreationForm etendu (Ch4)."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import NIVEAUX, ROLES, Utilisateur


class InscriptionForm(UserCreationForm):
    email = forms.EmailField(label="E-mail", required=True)
    role = forms.ChoiceField(
        label="Je suis",
        choices=[(r, l) for r, l in ROLES if r != "admin"],
        initial="apprenant",
    )
    niveau = forms.ChoiceField(label="Niveau", choices=NIVEAUX, initial="debutant")
    objectifs = forms.CharField(
        label="Mes objectifs",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )

    class Meta:
        model = Utilisateur
        fields = (
            "username",
            "email",
            "role",
            "niveau",
            "objectifs",
            "password1",
            "password2",
        )


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = [
            "first_name",
            "last_name",
            "email",
            "telephone",
            "niveau",
            "objectifs",
            "bio",
            "avatar",
        ]
        widgets = {
            "objectifs": forms.Textarea(attrs={"rows": 3}),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
