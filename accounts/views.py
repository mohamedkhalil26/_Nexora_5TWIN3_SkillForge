"""Vues accounts — Ch4/Ch5/Ch6 : inscription, profil, login/logout generiques."""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from learning.models import Competence

from . import ai
from .forms import InscriptionForm, ProfilForm
from .models import Utilisateur

User = get_user_model()


class InscriptionView(CreateView):
    """Register (Ch4) : UserCreationForm etendu."""

    model = Utilisateur
    form_class = InscriptionForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["suggestions_bio"] = "L'IA vous suggérera une bio après inscription."
        return ctx


class ProfilDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Utilisateur
    template_name = "accounts/profil_detail.html"
    context_object_name = "profil"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.pk == obj.pk or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.object
        if user.est_apprenant:
            # IA accounts : competences recommandees depuis les objectifs.
            ctx["recommandations"] = ai.recommander_competences(
                user.objectifs, list(Competence.objects.all())
            )
        return ctx


class ProfilUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Utilisateur
    form_class = ProfilForm
    template_name = "accounts/profil_form.html"

    def test_func(self):
        obj = self.get_object()
        return self.request.user.pk == obj.pk or self.request.user.is_staff
