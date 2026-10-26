"""API dashboard — Workshop API : stats par role + insight IA."""
from django.db.models import Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from certification.models import Certificat
from dashboard.ai import insight_apprenant, stats_plateforme
from quizzes.models import Tentative


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def mon_resume(request):
    user = request.user
    if getattr(user, "est_mentor", False):
        from mentoring.models import Reservation

        nb = Reservation.objects.filter(disponibilite__mentor__mentor=user).count()
        return Response({"role": "mentor", "reservations": nb})
    if user.is_staff or getattr(user, "est_admin", False):
        return Response({"role": "admin", **stats_plateforme()})
    scores = list(Tentative.objects.filter(apprenant=user).values_list("score", flat=True))
    moyenne = round(sum(scores) / len(scores), 1) if scores else 0.0
    stats = {"quiz_passes": len(scores), "moyenne": moyenne, "progression": 1 if scores else 0}
    return Response(
        {
            "role": "apprenant",
            **stats,
            "certificats": Certificat.objects.filter(apprenant=user).count(),
            "insight_ia": insight_apprenant(stats),
        }
    )
