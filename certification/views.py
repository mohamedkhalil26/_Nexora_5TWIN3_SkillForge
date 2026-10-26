"""Vues certification — Malek : demande, delivrance (eligibilite auto), PDF."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from learning.models import Competence

from . import ai
from .models import Certificat, est_eligible
from .pdf import generer_certificat_pdf


class CertificatListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Certificat
    template_name = "certification/certificat_list.html"
    context_object_name = "certificats"

    def get_queryset(self):
        qs = Certificat.objects.select_related("competence", "apprenant")
        if self.request.user.is_staff:
            return qs
        return qs.filter(apprenant=self.request.user)


class CertificatDetailView(LoginRequiredMixin, DetailView):
    model = Certificat
    template_name = "certification/certificat_detail.html"
    context_object_name = "certificat"

    def get_queryset(self):
        qs = Certificat.objects.select_related("competence", "apprenant")
        if self.request.user.is_staff:
            return qs
        return qs.filter(apprenant=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c = self.object
        ctx["feedback_ia"] = ai.feedback_certification(True, c.score_final, c.competence.nom)
        return ctx


class DemanderCertificatView(LoginRequiredMixin, View):
    """Demande pour une competence : verifie l'eligibilite puis delivre + PDF."""

    def post(self, request, slug):
        competence = get_object_or_404(Competence, slug=slug)
        eligible, moyenne = est_eligible(request.user, competence)
        if not eligible:
            messages.error(
                request,
                f"Pas encore éligible ({moyenne:.0f}% < 70%). Travaillez les quiz.",
            )
            return redirect("learning:competence-detail", slug=slug)
        cert, created = Certificat.objects.get_or_create(
            apprenant=request.user,
            competence=competence,
            defaults={"score_final": moyenne, "delivre_par": request.user},
        )
        if not created:
            messages.info(request, "Certificat déjà délivré.")
            return redirect("certification:certificat-detail", pk=cert.pk)
        cert.fichier.save(f"certificat-{cert.code}.pdf", ContentFile(generer_certificat_pdf(cert)))
        messages.success(request, f"Certificat « {competence.nom} » délivré !")
        return redirect("certification:certificat-detail", pk=cert.pk)


class TelechargerCertificatView(LoginRequiredMixin, View):
    def get(self, request, pk):
        cert = get_object_or_404(Certificat, pk=pk)
        if cert.apprenant != request.user and not request.user.is_staff:
            messages.error(request, "Accès refusé.")
            return redirect("certification:certificat-list")
        if not cert.fichier:
            cert.fichier.save(
                f"certificat-{cert.code}.pdf", ContentFile(generer_certificat_pdf(cert))
            )
        return FileResponse(cert.fichier.open("rb"), content_type="application/pdf")
