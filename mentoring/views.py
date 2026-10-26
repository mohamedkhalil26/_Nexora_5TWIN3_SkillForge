"""Vues mentoring — Raed : catalogue mentors, disponibilites, reservations, messagerie."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin
from quizzes.models import Tentative

from . import ai
from .forms import DisponibiliteForm, MentorProfileForm, MessageForm, ReservationForm
from .models import Disponibilite, MentorProfile, Reservation


class MentorListView(ListView):
    paginate_by = 12
    model = MentorProfile
    template_name = "mentoring/mentor_list.html"
    context_object_name = "mentors"

    def get_queryset(self):
        return MentorProfile.objects.filter(verifie=True).select_related("mentor").prefetch_related("specialites")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated and getattr(
            self.request.user, "est_apprenant", False
        ):
            # IA mentoring : top 3 mentors pour CET apprenant.
            ctx["recommandes"] = ai.recommander_mentors(
                self.request.user, list(self.get_queryset())
            )
        return ctx


class MentorDetailView(DetailView):
    model = MentorProfile
    template_name = "mentoring/mentor_detail.html"
    context_object_name = "mentor"

    def get_context_data(self, **kwargs):
        from django.utils import timezone

        ctx = super().get_context_data(**kwargs)
        ctx["dispos"] = self.object.disponibilites.filter(
            reserve=False, debut__gte=timezone.now()
        ).order_by("debut")[:10]
        ctx["suggestions"] = ai.suggerer_creneaux(self.object)
        return ctx


class MonProfilMentorView(RoleRequiredMixin, UpdateView):
    """Correctif roles n°1 : seul un mentor (ou admin/staff) a un profil mentor."""

    allowed_roles = ["mentor"]
    model = MentorProfile
    form_class = MentorProfileForm
    template_name = "mentoring/profil_form.html"

    def get_object(self, queryset=None):
        profil, _ = MentorProfile.objects.get_or_create(mentor=self.request.user)
        return profil


class DisponibiliteCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["mentor"]
    model = Disponibilite
    form_class = DisponibiliteForm
    template_name = "mentoring/disponibilite_form.html"

    def form_valid(self, form):
        profil, _ = MentorProfile.objects.get_or_create(mentor=self.request.user)
        form.instance.mentor = profil
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.mentor.get_absolute_url()


class ReserverView(LoginRequiredMixin, View):
    """Correctif roles n°2 : seuls les apprenants (ou le staff) peuvent réserver."""

    template_name = "mentoring/reserver.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (
            getattr(user, "est_apprenant", False)
            or user.is_staff
            or getattr(user, "est_admin", False)
        ):
            messages.error(request, "Seuls les apprenants peuvent réserver une session.")
            return redirect("mentoring:mentor-list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, dispo_pk):
        dispo = get_object_or_404(Disponibilite, pk=dispo_pk, reserve=False)
        form = ReservationForm()
        # IA : fiche de contexte pour motiver la demande.
        tentatives = list(
            Tentative.objects.filter(apprenant=request.user).order_by("-date")[:5]
        )
        fiche = ai.fiche_preparation(request.user, tentatives)
        return render(
            request, self.template_name, {"dispo": dispo, "form": form, "fiche": fiche}
        )

    def post(self, request, dispo_pk):
        dispo = get_object_or_404(Disponibilite, pk=dispo_pk, reserve=False)
        # Correctif roles n°2 (web) : pas d'auto-réservation de son propre créneau.
        if dispo.mentor.mentor_id == request.user.pk:
            messages.error(request, "Vous ne pouvez pas réserver votre propre créneau.")
            return redirect("mentoring:mentor-list")
        form = ReservationForm(request.POST)
        if form.is_valid():
            resa = form.save(commit=False)
            resa.disponibilite = dispo
            resa.apprenant = request.user
            resa.save()
            dispo.reserve = True
            dispo.save(update_fields=["reserve"])
            messages.success(request, "Réservation envoyée au mentor.")
            return redirect("mentoring:reservation-detail", pk=resa.pk)
        return render(request, self.template_name, {"dispo": dispo, "form": form})


class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "mentoring/reservation_detail.html"
    context_object_name = "reservation"

    def get_queryset(self):
        qs = Reservation.objects.select_related(
            "disponibilite__mentor__mentor", "apprenant"
        ).prefetch_related("messages__auteur")
        user = self.request.user
        if user.is_staff:
            return qs
        from django.db.models import Q

        return qs.filter(
            Q(apprenant=user) | Q(disponibilite__mentor__mentor=user)
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_message"] = MessageForm()
        ctx["peut_confirmer"] = (
            self.request.user == self.object.mentor and self.object.statut == "en_attente"
        )
        return ctx


class ConfirmerReservationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        resa = get_object_or_404(Reservation, pk=pk)
        if request.user != resa.mentor and not request.user.is_staff:
            messages.error(request, "Seul le mentor peut confirmer.")
            return redirect("mentoring:reservation-detail", pk=pk)
        resa.statut = " confirmee".strip()
        resa.generer_lien_visio()
        resa.save(update_fields=["statut", "lien_visio"])
        messages.success(request, "Session confirmée. Lien visio généré.")
        return redirect("mentoring:reservation-detail", pk=pk)


class EnvoyerMessageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.db.models import Q

        from .models import Message as Msg

        qs = Reservation.objects.select_related("disponibilite__mentor__mentor", "apprenant")
        if not request.user.is_staff:
            qs = qs.filter(
                Q(apprenant=request.user) | Q(disponibilite__mentor__mentor=request.user)
            )
        resa = get_object_or_404(qs, pk=pk)
        form = MessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.reservation = resa
            msg.auteur = request.user
            msg.save()
        return redirect("mentoring:reservation-detail", pk=pk)


class MesReservationsView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Reservation
    template_name = "mentoring/mes_reservations.html"
    context_object_name = "reservations"

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q

        return (
            Reservation.objects.filter(
                Q(apprenant=user) | Q(disponibilite__mentor__mentor=user)
            )
            .select_related("disponibilite__mentor__mentor", "apprenant")
            .order_by("-cree_le")
        )


class DisponibiliteUpdateView(RoleRequiredMixin, UpdateView):
    """CRUD Dispo : modification par le mentor proprietaire (si non reservee)."""

    allowed_roles = ["mentor"]
    model = Disponibilite
    form_class = DisponibiliteForm
    template_name = "mentoring/disponibilite_form.html"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(mentor__mentor=self.request.user, reserve=False)

    def get_success_url(self):
        return self.object.mentor.get_absolute_url()


class DisponibiliteDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Disponibilite
    template_name = "mentoring/disponibilite_confirm_delete.html"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(mentor__mentor=self.request.user, reserve=False)

    def get_success_url(self):
        from django.urls import reverse
        return reverse("mentoring:mes-reservations")
