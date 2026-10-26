"""Serializers learning — Workshop API : ModelSerializer, fields explicites."""
from rest_framework import serializers

from learning.models import Competence, Cours, Module, Ressource


class CompetenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competence
        fields = ["id", "nom", "description", "slug"]


class RessourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ressource
        fields = ["id", "module", "titre", "type", "url", "fichier"]


class ModuleSerializer(serializers.ModelSerializer):
    ressources = RessourceSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "cours", "titre", "contenu", "ordre", "ressources"]


class CoursSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Cours
        fields = [
            "id",
            "titre",
            "slug",
            "description",
            "duree_minutes",
            "publie",
            "competence",
            "modules",
        ]
