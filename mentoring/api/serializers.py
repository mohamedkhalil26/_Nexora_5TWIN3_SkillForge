"""Serializers mentoring — Workshop API."""
from rest_framework import serializers

from mentoring.models import Disponibilite, MentorProfile, Reservation


class MentorProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="mentor.username", read_only=True)

    class Meta:
        model = MentorProfile
        fields = ["id", "username", "presentation", "tarif", "verifie"]


class DisponibiliteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disponibilite
        fields = ["id", "mentor", "debut", "fin", "reserve"]
        read_only_fields = ["id", "reserve"]


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ["id", "disponibilite", "sujet", "statut", "lien_visio", "cree_le"]
        read_only_fields = ["id", "statut", "lien_visio", "cree_le"]
