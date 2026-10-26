"""Formulaires learning — Ch6 : ModelForm, fields explicites."""
from django import forms

from .models import Competence, Cours, Module, Ressource


class CompetenceForm(forms.ModelForm):
    class Meta:
        model = Competence
        fields = ["nom", "description", "slug", "image"]


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ["competence", "titre", "slug", "description", "duree_minutes", "publie"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ["cours", "titre", "contenu", "ordre"]
        widgets = {"contenu": forms.Textarea(attrs={"rows": 8})}


class RessourceForm(forms.ModelForm):
    class Meta:
        model = Ressource
        fields = ["module", "titre", "type", "url", "fichier"]
