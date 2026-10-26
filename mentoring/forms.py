"""Formulaires mentoring — Ch6 : ModelForm CRUD + reservation + message."""
from django import forms

from .models import Disponibilite, MentorProfile, Message, Reservation


class MentorProfileForm(forms.ModelForm):
    class Meta:
        model = MentorProfile
        fields = ["presentation", "tarif", "specialites"]
        widgets = {"presentation": forms.Textarea(attrs={"rows": 4})}


class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ["debut", "fin"]

    def clean(self):
        data = super().clean()
        debut, fin = data.get("debut"), data.get("fin")
        from django.utils import timezone
        if debut and debut < timezone.now():
            self.add_error("debut", "Le créneau doit être dans le futur.")
        if debut and fin and fin <= debut:
            self.add_error("fin", "La fin doit être après le début.")
        return data
        widgets = {
            "debut": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "fin": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["sujet"]


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["contenu"]
        widgets = {"contenu": forms.Textarea(attrs={"rows": 2})}
