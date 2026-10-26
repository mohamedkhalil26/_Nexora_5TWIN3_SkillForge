"""Vues learning — Ch6 : Display views pour apprenants, Editing views pour staff."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin

from . import ai
from .forms import CompetenceForm, CoursForm, ModuleForm, RessourceForm
from .models import Competence, Cours, Module, Ressource


class CompetenceListView(ListView):
    paginate_by = 12
    model = Competence
    template_name = "learning/competence_list.html"
    context_object_name = "competences"


class CompetenceDetailView(DetailView):
    model = Competence
    template_name = "learning/competence_detail.html"
    context_object_name = "competence"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cours"] = self.object.cours.filter(publie=True)
        return ctx


class CoursListView(ListView):
    paginate_by = 12
    model = Cours
    template_name = "learning/cours_list.html"
    context_object_name = "cours"

    def get_queryset(self):
        qs = Cours.objects.filter(publie=True).select_related("competence")
        q = self.request.GET.get("q", "").strip()
        comp = self.request.GET.get("competence", "").strip()
        if comp:
            qs = qs.filter(competence__slug=comp)
        if q:
            # IA learning : recherche semantique locale sur le catalogue.
            qs = ai.recherche_semantique(q, list(qs), top=20)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["competences"] = Competence.objects.all()
        return ctx


class CoursDetailView(DetailView):
    model = Cours
    template_name = "learning/cours_detail.html"
    context_object_name = "cours"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["modules"] = self.object.modules.prefetch_related("ressources")
        ctx["similaires"] = ai.cours_similaires(
            self.object, list(Cours.objects.filter(publie=True))
        )
        ctx["quiz"] = self.object.quiz.filter(actif=True)
        return ctx


class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = Module
    template_name = "learning/module_detail.html"
    context_object_name = "module"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["resume_ia"] = ai.resumer_module(self.object.contenu)
        ctx["tags"] = ai.auto_tags(self.object.titre, self.object.contenu)
        return ctx


class CoursCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["mentor"]
    model = Cours
    form_class = CoursForm
    template_name = "learning/cours_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        form.instance.auteur = self.request.user
        return super().form_valid(form)


class CoursUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["mentor"]
    model = Cours
    form_class = CoursForm
    template_name = "learning/cours_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class CoursDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Cours
    template_name = "learning/cours_confirm_delete.html"
    success_url = reverse_lazy("learning:cours-list")


class ModuleCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["mentor"]
    model = Module
    form_class = ModuleForm
    template_name = "learning/module_form.html"

    def get_success_url(self):
        # Point 11 : utilise get_absolute_url() du Module (-> module-detail).
        return self.object.get_absolute_url()


class ModuleUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["mentor"]
    model = Module
    form_class = ModuleForm
    template_name = "learning/module_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class CompetenceCreateView(RoleRequiredMixin, CreateView):
    """CRUD Competence : creation reservee aux mentors (admin bypass)."""

    allowed_roles = ["mentor"]
    model = Competence
    form_class = CompetenceForm
    template_name = "learning/competence_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class CompetenceUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["mentor"]
    model = Competence
    form_class = CompetenceForm
    template_name = "learning/competence_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class CompetenceDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Competence
    template_name = "learning/competence_confirm_delete.html"
    success_url = reverse_lazy("learning:competence-list")


class ModuleDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Module
    template_name = "learning/module_confirm_delete.html"

    def get_success_url(self):
        return self.object.cours.get_absolute_url()


class RessourceCreateView(RoleRequiredMixin, CreateView):
    """CRUD Ressource : ajout de PDF/lien/video a un module."""

    allowed_roles = ["mentor"]
    model = Ressource
    form_class = RessourceForm
    template_name = "learning/ressource_form.html"

    def get_initial(self):
        initial = super().get_initial()
        module_pk = self.request.GET.get("module")
        if module_pk:
            initial["module"] = module_pk
        return initial

    def get_success_url(self):
        return self.object.module.get_absolute_url()


class RessourceUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["mentor"]
    model = Ressource
    form_class = RessourceForm
    template_name = "learning/ressource_form.html"

    def get_success_url(self):
        return self.object.module.get_absolute_url()


class RessourceDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Ressource
    template_name = "learning/ressource_confirm_delete.html"

    def get_success_url(self):
        return self.object.module.get_absolute_url()
