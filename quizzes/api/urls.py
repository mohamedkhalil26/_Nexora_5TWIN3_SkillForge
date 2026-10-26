from django.urls import path

from .views import (
    detail_question,
    detail_quiz,
    generer_questions,
    liste_quiz,
    mes_tentatives,
    questions,
    soumettre_quiz,
)

app_name = "quizzes-api"

urlpatterns = [
    path("", liste_quiz, name="liste-quiz"),
    path("<int:pk>/", detail_quiz, name="detail-quiz"),
    path("<int:pk>/soumettre/", soumettre_quiz, name="soumettre-quiz"),
    path("mes-tentatives/", mes_tentatives, name="mes-tentatives"),
    path("questions/", questions, name="questions"),
    path("questions/<int:pk>/", detail_question, name="detail-question"),
    path("generer-questions/", generer_questions, name="generer-questions"),
]
