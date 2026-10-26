"""Serializers certification — Workshop API."""
from rest_framework import serializers

from certification.models import Certificat


class CertificatSerializer(serializers.ModelSerializer):
    competence = serializers.CharField(source="competence.nom", read_only=True)

    class Meta:
        model = Certificat
        fields = ["id", "competence", "score_final", "code", "delivre_le"]
        read_only_fields = ["id", "competence", "score_final", "code", "delivre_le"]
