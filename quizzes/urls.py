from django.urls import path

from .views import (
    MesTentativesView,
    PasserQuizView,
    QuestionCreateView,
    QuestionDeleteView,
    QuestionListView,
    QuestionUpdateView,
    QuizCreateView,
    QuizDeleteView,
    QuizDetailView,
    QuizListView,
    QuizUpdateView,
    TentativeDetailView,
)

app_name = "quizzes"

urlpatterns = [
    path("", QuizListView.as_view(), name="quiz-list"),
    path("nouveau/", QuizCreateView.as_view(), name="quiz-create"),
    path("questions/nouvelle/", QuestionCreateView.as_view(), name="question-create"),
    path("<int:pk>/modifier/", QuizUpdateView.as_view(), name="quiz-update"),
    path("<int:pk>/supprimer/", QuizDeleteView.as_view(), name="quiz-delete"),
    path("<int:pk>/questions/", QuestionListView.as_view(), name="question-list"),
    path(
        "questions/<int:pk>/modifier/",
        QuestionUpdateView.as_view(),
        name="question-update",
    ),
    path(
        "questions/<int:pk>/supprimer/",
        QuestionDeleteView.as_view(),
        name="question-delete",
    ),
    path("mes-tentatives/", MesTentativesView.as_view(), name="mes-tentatives"),
    path("<int:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("<int:pk>/passer/", PasserQuizView.as_view(), name="quiz-passer"),
    path("tentatives/<int:pk>/", TentativeDetailView.as_view(), name="tentative-detail"),
]
