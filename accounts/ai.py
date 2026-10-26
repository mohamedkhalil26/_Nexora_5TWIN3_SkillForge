"""IA accounts (INDEPENDANTE) — Khalil.
Reco initiales + completion bio (local sklearn, Gemini optionnel).
Pattern workshop AI : fonction -> vue JsonResponse -> bouton fetch.
"""
from django.conf import settings

from common.text import normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False


def gemini_generate(prompt: str) -> str | None:
    """Gemini optionnel : None si pas de cle (fallback local)."""
    if not getattr(settings, "GOOGLE_API_KEY", ""):
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(prompt).text
    except Exception:
        return None


def recommander_competences(objectifs: str, competences: list) -> list:
    """Top 3 competences via TF-IDF local sur (nom + description)."""
    if not objectifs or not competences or not _SKLEARN_OK:
        return list(competences)[:3]
    docs = [f"{c.nom} {c.description}" for c in competences]
    try:
        vec = TfidfVectorizer()
        mat = vec.fit_transform([normalize(objectifs)] + [normalize(d) for d in docs])
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        ranked = sorted(zip(competences, sims), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:3]]
    except Exception:
        return list(competences)[:3]


def suggerer_bio(objectifs: str, niveau: str) -> str:
    """Suggestion de bio : Gemini si cle, sinon template local."""
    gemini = gemini_generate(
        f"Rédige en 3 lignes la bio d'un apprenant de niveau {niveau} "
        f"dont l'objectif est : {objectifs}. En français."
    )
    if gemini:
        return gemini
    obj = (objectifs or "développer mes compétences").strip()
    return (
        f"Apprenant de niveau {niveau}, motivé par l'objectif suivant : {obj}. "
        "Je souhaite suivre un parcours structuré, pratiquer avec des quiz "
        "et être accompagné par un mentor."
    )
