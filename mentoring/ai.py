"""IA mentoring (INDEPENDANTE) — Raed : matching, creneaux, fiche de preparation."""
from django.conf import settings

from common.text import normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False


def gemini_generate(prompt: str) -> str | None:
    if not getattr(settings, "GOOGLE_API_KEY", ""):
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
    except Exception:
        return None


def score_mentor(apprenant, profil) -> float:
    """Score 0-100 : specialites communes (60) + disponibilites libres (25) + verifie (15)."""
    score = 0.0
    objectifs = normalize(getattr(apprenant, "objectifs", "") or "")
    specs = list(profil.specialites.all())
    if specs and _SKLEARN_OK and objectifs:
        try:
            docs = [f"{s.nom} {s.description}" for s in specs]
            vec = TfidfVectorizer()
            mat = vec.fit_transform([objectifs] + [normalize(d) for d in docs])
            sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
            score += float(max(sims)) * 60
        except Exception:
            if any(normalize(s.nom) in objectifs for s in specs):
                score += 40
    elif specs and objectifs:
        if any(normalize(s.nom) in objectifs for s in specs):
            score += 40
    libres = profil.disponibilites.filter(reserve=False).count()
    score += min(libres * 5, 25)
    if profil.verifie:
        score += 15
    return round(min(score, 100), 1)


def recommander_mentors(apprenant, profils: list, top: int = 3) -> list:
    return sorted(profils, key=lambda p: score_mentor(apprenant, p), reverse=True)[:top]


def suggerer_creneaux(profil, duree_min: int = 60) -> list:
    """Creneaux libres assez longs, tries par proximite."""
    from django.utils import timezone

    now = timezone.now()
    dispos = profil.disponibilites.filter(reserve=False, debut__gte=now).order_by("debut")
    return [d for d in dispos if (d.fin - d.debut).total_seconds() >= duree_min * 60][:5]


def fiche_preparation(apprenant, tentatives: list) -> str:
    """Fiche mentor : progression + points faibles (Gemini si cle, sinon regles)."""
    lignes = []
    for t in tentatives[:5]:
        lignes.append(f"- {t.quiz.titre} : {t.score:.0f}% ({'réussi' if t.reussi else 'à retravailler'})")
    resume = "\n".join(lignes) or "Aucune tentative pour l'instant."
    gemini = gemini_generate(
        "Tu prépares un mentor pour sa session. Profil apprenant : "
        f"niveau {getattr(apprenant, 'niveau', '?')}, objectifs : "
        f"{getattr(apprenant, 'objectifs', '?')}. Historique quiz :\n{resume}\n"
        "Rédige une fiche de préparation en français : 3 points forts/faibles + 2 sujets à aborder."
    )
    if gemini:
        return gemini
    faibles = [t for t in tentatives[:5] if not t.reussi]
    reco = (
        "Revoir : " + ", ".join(t.quiz.titre for t in faibles)
        if faibles
        else "Consolider les acquis et viser la certification."
    )
    return (
        f"Fiche de préparation — {apprenant.username} "
        f"(niveau {getattr(apprenant, 'niveau', '?')}).\n"
        f"Historique récent :\n{resume}\nRecommandation : {reco}"
    )
