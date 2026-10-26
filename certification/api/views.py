"""API certification — Workshop API : mes certificats + eligibilite IA + demande."""
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from certification import ai
from certification.models import Certificat, est_eligible
from certification.pdf import generer_certificat_pdf
from learning.models import Competence

from .serializers import CertificatSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_certificats(request):
    qs = Certificat.objects.filter(apprenant=request.user).select_related("competence")
    return Response(CertificatSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def eligibilite(request, slug):
    competence = get_object_or_404(Competence, slug=slug)
    eligible, moyenne = est_eligible(request.user, competence)
    proba, message = ai.predire_reussite(
        list(
            request.user.tentatives.filter(quiz__cours__competence=competence).values_list(
                "score", flat=True
            )
        )
    )
    return Response(
        {
            "competence": competence.nom,
            "eligible": eligible,
            "moyenne": moyenne,
            "probabilite_ia": proba,
            "message_ia": message,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def demander(request, slug):
    competence = get_object_or_404(Competence, slug=slug)
    eligible, moyenne = est_eligible(request.user, competence)
    if not eligible:
        return Response(
            {"detail": f"Pas encore éligible ({moyenne:.0f}% < 70%)."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        cert = Certificat.objects.create(
            apprenant=request.user, competence=competence, score_final=moyenne
        )
    except IntegrityError:
        cert = Certificat.objects.get(apprenant=request.user, competence=competence)
        return Response(CertificatSerializer(cert).data)
    cert.fichier.save(
        f"certificat-{cert.code}.pdf", ContentFile(generer_certificat_pdf(cert))
    )
    return Response(CertificatSerializer(cert).data, status=status.HTTP_201_CREATED)
