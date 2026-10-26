"""IA dashboard (INDEPENDANTE) — Malek : insights en langage naturel + stats."""
from django.conf import settings


def gemini_generate(prompt: str) -> str | None:
    if not getattr(settings, "GOOGLE_API_KEY", ""):
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
    except Exception:
        return None


def insight_apprenant(stats: dict) -> str:
    """Phrase personnalisee depuis les stats (Gemini si cle, sinon templates)."""
    gemini = gemini_generate(
        "Tu es le coach SkillForge. Stats de l'apprenant : "
        f"{stats}. Donne 1 insight motivant en français (3 lignes max) "
        "avec 1 recommandation d'action précise."
    )
    if gemini:
        return gemini
    moyenne = stats.get("moyenne", 0) or 0
    progression = stats.get("progression", 0) or 0
    quiz = stats.get("quiz_passes", 0) or 0
    if quiz == 0:
        return (
            "Bienvenue sur SkillForge ! Passez votre premier quiz pour "
            "activer vos recommandations personnalisées."
        )
    if moyenne >= 85:
        return (
            f"Excellent : {moyenne:.0f}% de moyenne sur {quiz} quiz. "
            "Visez la certification de votre prochaine compétence."
        )
    if progression and progression > 0:
        return (
            f"En progrès : {moyenne:.0f}% de moyenne. "
            "Reprenez les quiz sous 70% puis réservez une session mentor."
        )
    return (
        f"Moyenne actuelle : {moyenne:.0f}% sur {quiz} quiz. "
        "Reprenez les modules faibles et retentez les quiz."
    )


def stats_plateforme() -> dict:
    """Agregats admin (ORM uniquement, Ch2 QuerySets)."""
    from django.contrib.auth import get_user_model

    from certification.models import Certificat
    from learning.models import Cours
    from mentoring.models import Reservation
    from quizzes.models import Tentative

    User = get_user_model()
    return {
        "utilisateurs": User.objects.count(),
        "apprenants": User.objects.filter(role="apprenant").count(),
        "mentors": User.objects.filter(role="mentor").count(),
        "cours": Cours.objects.filter(publie=True).count(),
        "tentatives": Tentative.objects.count(),
        "reservations": Reservation.objects.count(),
        "certificats": Certificat.objects.count(),
    }
