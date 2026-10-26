"""API accounts — Workshop API + Workshop AI : @api_view + JsonResponse IA."""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts import ai
from accounts.models import Utilisateur

from .serializers import UtilisateurSerializer


@api_view(["GET", "PUT"])
@permission_classes([IsAuthenticated])
def mon_profil(request):
    """GET / PUT sur son propre profil (jamais celui des autres)."""
    user = request.user
    if request.method == "GET":
        return Response(UtilisateurSerializer(user).data)
    serializer = UtilisateurSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def liste_apprenants(request):
    if not (request.user.is_staff or request.user.role == "mentor"):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    qs = Utilisateur.objects.filter(role="apprenant").order_by("username")[:50]
    return Response(UtilisateurSerializer(qs, many=True).data)


def suggerer_bio(request):
    """Endpoint IA accounts (pattern workshop AI : POST JSON + JsonResponse).

    Correctif roles n°5 : reste PUBLIC par design — son seul appelant est le
    bouton "Suggérer ma bio" de la page d'inscription (visiteurs anonymes).
    Coût faible (texte court), pas de clé facturée si absente (fallback local).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST requis."}, status=400)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "JSON invalide."}, status=400)
    bio = ai.suggerer_bio(data.get("objectifs", ""), data.get("niveau", "debutant"))
    return JsonResponse({"bio": bio})
