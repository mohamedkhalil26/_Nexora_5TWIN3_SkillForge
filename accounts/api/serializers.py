"""Serializers accounts — Workshop API : ModelSerializer, fields explicites."""
from rest_framework import serializers

from accounts.models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "niveau",
            "objectifs",
            "bio",
        ]
        read_only_fields = ["id", "username"]
