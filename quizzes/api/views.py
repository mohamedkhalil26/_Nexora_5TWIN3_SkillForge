"""API quizzes — Workshop API + Workshop AI : CRUD quiz + correction + generation."""
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from quizzes import ai
from quizzes.models import Question, Quiz, Reponse, Tentative

from .serializers import QuestionSerializer, QuizSerializer, TentativeSerializer


def _est_mentor_ou_staff(user):
    return user.is_authenticated and (
        user.is_staff or getattr(user, "role", None) == "mentor"
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def liste_quiz(request):
    qs = Quiz.objects.filter(actif=True).select_related("cours")
    return Response(QuizSerializer(qs, many=True).data)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def detail_quiz(request, pk):
    # Correctif roles n4 (parite web) : GET public pour quiz actifs,
    # PUT/DELETE staff uniquement.
    quiz = get_object_or_404(Quiz, pk=pk)
    if request.method == "GET":
        if not quiz.actif and not (request.user.is_authenticated and request.user.is_staff):
            return Response({"detail": "Non publie."}, status=status.HTTP_403_FORBIDDEN)
        return Response(QuizSerializer(quiz).data)
    if not (request.user.is_authenticated and request.user.is_staff):
        return Response({"detail": "Réservé au staff."}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "PUT":
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    quiz.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def soumettre_quiz(request, pk):
    """POST {reponses: {question_id: valeur}} -> correction IA + tentative."""
    # Correctif roles n°3 (API) : seuls les apprenants (ou staff/admin) passent un quiz.
    if not (
        getattr(request.user, "est_apprenant", False)
        or request.user.is_staff
        or getattr(request.user, "est_admin", False)
    ):
        return Response(
            {"detail": "Seuls les apprenants peuvent passer un quiz."},
            status=status.HTTP_403_FORBIDDEN,
        )
    quiz = get_object_or_404(Quiz, pk=pk, actif=True)
    donnees = request.data.get("reponses", {})
    tentative = Tentative.objects.create(quiz=quiz, apprenant=request.user)
    questions = list(quiz.questions.all())
    total = sum(q.points for q in questions) or 1
    obtenus = 0.0
    for q in questions:
        donnee = str(donnees.get(str(q.pk), donnees.get(q.pk, "")))
        if q.type == "qcm":
            ok, pts = ai.corriger_qcm(q, donnee)
        else:
            ok, pts, _ = ai.corriger_libre(q, donnee)
        obtenus += pts
        Reponse.objects.create(
            tentative=tentative,
            question=q,
            reponse_donnee=donnee,
            correct=ok,
            points_obtenus=pts,
        )
    tentative.score = round(obtenus / total * 100, 1)
    tentative.reussi = tentative.score >= quiz.seuil_reussite
    tentative.feedback = ai.feedback_quiz(tentative.reussi, tentative.score)
    tentative.save()
    return Response(TentativeSerializer(tentative).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mes_tentatives(request):
    qs = Tentative.objects.filter(apprenant=request.user).order_by("-date")[:20]
    return Response(TentativeSerializer(qs, many=True).data)


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def questions(request):
    """CRUD Question : GET public (?quiz=<id>), POST mentor/staff."""
    if request.method == "GET":
        qs = Question.objects.select_related("quiz")
        quiz_id = request.GET.get("quiz")
        if quiz_id:
            qs = qs.filter(quiz_id=quiz_id)
        return Response(QuestionSerializer(qs[:100], many=True).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    serializer = QuestionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([AllowAny])
def detail_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == "GET":
        return Response(QuestionSerializer(question).data)
    if not _est_mentor_ou_staff(request.user):
        return Response({"detail": "Réservé aux mentors."}, status=status.HTTP_403_FORBIDDEN)
    if request.method == "PUT":
        serializer = QuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    question.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@login_required
def generer_questions(request):
    """Endpoint IA quizzes (workshop AI) : QCM auto depuis un contenu.

    Correctif roles n°5 : login requis (anti-spam clé IA).
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST requis."}, status=400)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({"error": "JSON invalide."}, status=400)
    contenu = (data.get("contenu") or "").strip()
    if not contenu:
        return JsonResponse({"error": "Contenu requis."}, status=400)
    try:
        nb = max(1, min(int(data.get("nb", 3)), 10))
    except (TypeError, ValueError):
        nb = 3
    return JsonResponse({"questions": ai.generer_qcm(contenu, nb=nb)})
