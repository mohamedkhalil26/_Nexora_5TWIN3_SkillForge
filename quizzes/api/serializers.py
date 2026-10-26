"""Serializers quizzes — Workshop API."""
from rest_framework import serializers

from quizzes.models import Question, Quiz, Tentative


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "quiz", "type", "enonce", "choix", "bonne_reponse", "points", "ordre"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "titre", "seuil_reussite", "actif", "cours", "questions"]


class TentativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tentative
        fields = ["id", "quiz", "score", "reussi", "feedback", "date"]
        read_only_fields = ["id", "score", "reussi", "feedback", "date"]
