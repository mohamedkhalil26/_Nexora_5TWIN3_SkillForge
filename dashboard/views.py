"""Vues dashboard — Malek : landing, home par role, stats admin (Ch2 agregats)."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count
from django.views.generic import TemplateView

from .ai import insight_apprenant, stats_plateforme


class LandingView(TemplateView):
    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        from learning.models import Competence

        ctx = super().get_context_data(**kwargs)
        ctx["competences"] = Competence.objects.all()[:6]
        return ctx


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        from certification.models import Certificat
        from learning.models import Competence
        from mentoring.models import Reservation
        from quizzes.models import Tentative

        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["user"] = user
        if getattr(user, "est_apprenant", False):
            tentatives = Tentative.objects.filter(apprenant=user).select_related("quiz")
            scores = list(tentatives.values_list("score", flat=True))
            moyenne = sum(scores) / len(scores) if scores else 0
            ctx["tentatives"] = tentatives.order_by("-date")[:5]
            ctx["certificats"] = Certificat.objects.filter(apprenant=user)[:5]
            ctx["reservations"] = Reservation.objects.filter(apprenant=user).order_by(
                "-cree_le"
            )[:5]
            ctx["stats"] = {
                "quiz_passes": len(scores),
                "moyenne": round(moyenne, 1),
                "progression": 1 if scores else 0,
            }
            ctx["insight_ia"] = insight_apprenant(ctx["stats"])
        elif getattr(user, "est_mentor", False):
            ctx["reservations"] = (
                Reservation.objects.filter(disponibilite__mentor__mentor=user)
                .select_related("disponibilite", "apprenant")
                .order_by("-cree_le")[:10]
            )
            ctx["nb_apprenants"] = (
                Reservation.objects.filter(disponibilite__mentor__mentor=user)
                .values("apprenant")
                .distinct()
                .count()
            )
        else:
            ctx["stats"] = stats_plateforme()
            ctx["reussite"] = Tentative.objects.aggregate(m=Avg("score"))["m"] or 0
            ctx["top_cours"] = (
                Tentative.objects.values("quiz__cours__titre")
                .annotate(n=Count("id"))
                .order_by("-n")[:5]
            )
            ctx["competences"] = Competence.objects.all()
        return ctx
