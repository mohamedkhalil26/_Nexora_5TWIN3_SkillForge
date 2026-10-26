"""API learning — Workshop API : GET liste/detail, PUT staff, POST IA."""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from learning import ai
from learning.models import Competence, Cours, Module, Ressource

from .serializers import CompetenceSerializer, CoursSerializer, ModuleSerializer, RessourceSerializer


def _est_mentor_ou_staff(user):
    return user.is_authenticated and (
        user.is_staff or getattr(user, "role", None) == "mentor"
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_competences(request):
    qs = Competence.objects.all().order_by("nom")
    return Response(CompetenceSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_cours(request):
    qs = Cours.objects.filter(publie=True).select_related("competence")
    q = request.GET.get("q", "").strip()
    if q:
        qs = ai.recherche_semantique(q, list(qs), top=20)
    return Response(CoursSerializer(qs, many=True).data)


@api_view(["GET", "PUT"])
@permission_classes([AllowAny])
def detail_cours(request, slug):
    # Correctif roles n°4 (parité web) : GET public pour les cours publiés,
    # PUT réservé au staff ; non-publié visible par le staff uniquement.
    try:
        cours = Cours.objects.get(slug=slug)
    except Cours.DoesNotExist:
        return Response({"detail": "Introuvable."}, status=status.HTTP_404_NOT_FOUND)
    user = request.user
    if request.method == "GET":
        if not cours.publie and not (user.is_authenticated and user.is_staff):
            return Response({"detail": "Non publié."}, status=status.HTTP_403_FORBIDDEN)
        return Response(CoursSerializer(cours).data)
    if not (user.is_authenticated and user.is_staff):
        return Response({"detail": "Réservé au staff."}, status=status.HTTP_403_FORBIDDEN)
    serializer = CoursSerializer(cours, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
def generer_description(request):
    """Endpoint IA learning (workshop AI) : description depuis le titre.

    Correctif roles n°5 : login requis (anti-spam clé IA).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST requis."}, status=400)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "JSON invalide."}, status=400)
    titre = (data.get("titre") or "").strip()
    if not titre:
        return JsonResponse({"error": "Titre requis."}, status=400)
    return JsonResponse({"description": ai.generer_description(titre)})


@login_required
def generer_image(request):
    """Workshop AI partie 2 : image de couverture generee, sauvegardee en media/.

    Correctif roles n°5 : login requis (anti-spam clé IA).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST requis."}, status=400)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "JSON invalide."}, status=400)
    titre = (data.get("titre") or "").strip()
    if not titre:
        return JsonResponse({"error": "Titre requis."}, status=400)
    blob, erreur = ai.generer_image_cover(titre)
    if not blob:
        if erreur.startswith("network"):
            msg = f"Service d'image injoignable ({erreur}). Vérifiez internet / proxy / DNS."
        else:
            msg = f"Échec génération de la cover : {erreur}."
        return JsonResponse({"error": msg}, status=503)
    import os
    from django.conf import settings
    from django.utils.text import slugify

    os.makedirs(settings.MEDIA_ROOT / "covers", exist_ok=True)
    nom = f"covers/cover-{slugify(titre)[:40]}.jpg"
    with open(settings.MEDIA_ROOT / nom, "wb") as f:
        f.write(blob)
    return JsonResponse({"image_url": settings.MEDIA_URL + nom})


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def modules(request):
    """CRUD Module : GET public (?cours=<id>), POST mentor/staff."""
    if request.method == "GET":
        qs = Module.objects.select_related("cours").prefetch_related("ressources")
        cours_id = request.GET.get("cours")
        if cours_id:
            qs = qs.filter(cours_id=cours_id)
        return Response(ModuleSerializer(qs[:50], many=True).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    serializer = ModuleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def detail_module(request, pk):
    """GET public, PUT/DELETE mentor/staff."""
    module = get_object_or_404(Module, pk=pk)
    if request.method == "GET":
        return Response(ModuleSerializer(module).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "PUT":
        serializer = ModuleSerializer(module, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    module.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def ressources(request):
    """CRUD Ressource : GET public (?module=<id>), POST mentor/staff."""
    if request.method == "GET":
        qs = Ressource.objects.select_related("module")
        module_id = request.GET.get("module")
        if module_id:
            qs = qs.filter(module_id=module_id)
        return Response(RessourceSerializer(qs[:50], many=True).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    serializer = RessourceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def detail_ressource(request, pk):
    ressource = get_object_or_404(Ressource, pk=pk)
    if request.method == "GET":
        return Response(RessourceSerializer(ressource).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "PUT":
        serializer = RessourceSerializer(ressource, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    ressource.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
