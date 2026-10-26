"""API mentoring — Workshop API : dispos, reservation, annulation + fiche IA."""
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from mentoring import ai
from mentoring.models import Disponibilite, MentorProfile, Reservation
from quizzes.models import Tentative

from .serializers import (
    DisponibiliteSerializer,
    MentorProfileSerializer,
    ReservationSerializer,
)


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_mentors(request):
    qs = MentorProfile.objects.filter(verifie=True).select_related("mentor")
    data = MentorProfileSerializer(qs, many=True).data
    if request.user.is_authenticated and getattr(request.user, "est_apprenant", False):
        top = {m.pk for m in ai.recommander_mentors(request.user, list(qs))}
        for item in data:
            item["recommande"] = item["id"] in top
    return Response(data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def disponibilites(request):
    # Correctif roles : GET public (parite page web catalogue),
    # POST reserve aux mentors (ou staff).
    if request.method == "GET":
        qs = Disponibilite.objects.filter(reserve=False).order_by("debut")[:50]
        return Response(DisponibiliteSerializer(qs, many=True).data)
    if (
        not request.user.is_authenticated
        or (getattr(request.user, "role", None) != "mentor" and not request.user.is_staff)
    ):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    profil, _ = MentorProfile.objects.get_or_create(mentor=request.user)
    serializer = DisponibiliteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(mentor=profil)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reservations(request):
    user = request.user
    if request.method == "GET":
        qs = Reservation.objects.filter(
            Q(apprenant=user) | Q(disponibilite__mentor__mentor=user)
        ).order_by("-cree_le")
        return Response(ReservationSerializer(qs, many=True).data)
    # Correctif roles n°2 (API) : seuls les apprenants (ou staff/admin) réservent.
    if not (
        getattr(user, "est_apprenant", False)
        or user.is_staff
        or getattr(user, "est_admin", False)
    ):
        return Response(
            {"detail": "Seuls les apprenants peuvent réserver."},
            status=status.HTTP_403_FORBIDDEN,
        )
    dispo_id = request.data.get("disponibilite")
    dispo = get_object_or_404(Disponibilite, pk=dispo_id, reserve=False)
    if dispo.mentor.mentor_id == user.pk:
        return Response(
            {"detail": "Vous ne pouvez pas réserver votre propre créneau."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    serializer = ReservationSerializer(data=request.data)
    if serializer.is_valid():
        resa = serializer.save(disponibilite=dispo, apprenant=user)
        dispo.reserve = True
        dispo.save(update_fields=["reserve"])
        return Response(ReservationSerializer(resa).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def detail_disponibilite(request, pk):
    """GET public, PUT/DELETE mentor proprietaire (si non reservee) ou staff."""
    dispo = get_object_or_404(Disponibilite, pk=pk)
    if request.method == "GET":
        return Response(DisponibiliteSerializer(dispo).data)
    user = request.user
    if not (user.is_authenticated and (user.is_staff or getattr(user, "role", None) == "mentor")):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    if not user.is_staff and dispo.mentor.mentor_id != user.pk:
        return Response({"detail": "Pas votre créneau."}, status=status.HTTP_403_FORBIDDEN)
    if dispo.reserve and request.method in ("PUT", "DELETE"):
        return Response({"detail": "Créneau déjà réservé."}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == "PUT":
        serializer = DisponibiliteSerializer(dispo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    dispo.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def annuler_reservation(request, pk):
    user = request.user
    resa = get_object_or_404(
        Reservation.objects.filter(
            Q(apprenant=user) | Q(disponibilite__mentor__mentor=user)
        ),
        pk=pk,
    )
    resa.statut = "annulee"
    resa.save(update_fields=["statut"])
    resa.disponibilite.reserve = False
    resa.disponibilite.save(update_fields=["reserve"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def fiche_preparation(request):
    """Endpoint IA mentoring (workshop AI) : fiche pour le mentor.

    Correctif roles n°5 : login requis + réservé au mentor du créneau (ou staff).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST requis."}, status=400)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "JSON invalide."}, status=400)
    resa = get_object_or_404(Reservation, pk=data.get("reservation_id"))
    if request.user != resa.mentor and not request.user.is_staff:
        return JsonResponse({"error": "Réservé au mentor."}, status=403)
    tentatives = list(Tentative.objects.filter(apprenant=resa.apprenant).order_by("-date")[:5])
    return JsonResponse({"fiche": ai.fiche_preparation(resa.apprenant, tentatives)})
