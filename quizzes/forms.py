"""Formulaires quizzes — Ch6 : ModelForm pour le CRUD mentor + formulaire de passation."""
from django import forms

from .models import Question, Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["cours", "titre", "seuil_reussite", "actif"]


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["quiz", "type", "enonce", "choix", "bonne_reponse", "points", "ordre"]
        widgets = {
            "enonce": forms.Textarea(attrs={"rows": 3}),
            "choix": forms.Textarea(attrs={"rows": 4}),
            "bonne_reponse": forms.Textarea(attrs={"rows": 2}),
        }


class PasserQuizForm(forms.Form):
    """Formulaire dynamique construit en vue : un champ par question."""

    def __init__(self, *args, questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        for q in questions or []:
            if q.type == "qcm":
                self.fields[f"q_{q.pk}"] = forms.ChoiceField(
                    label=q.enonce,
                    choices=[(str(i + 1), c) for i, c in enumerate(q.liste_choix())],
                    widget=forms.RadioSelect,
                    required=True,
                )
            else:
                self.fields[f"q_{q.pk}"] = forms.CharField(
                    label=q.enonce, widget=forms.Textarea(attrs={"rows": 4}), required=False
                )
