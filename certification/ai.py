"""IA certification (INDEPENDANTE) — Malek : prediction reussite, anti-fraude, feedback."""
from django.conf import settings

from common.text import normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics.pairwise import cosine_similarity

    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False


_GEMINI_COOLDOWN = 300  # secondes : apres un echec, on n'essaie plus (perf grille 5.2)
_gemini_dernier_echec = 0.0


def gemini_generate(prompt: str) -> str | None:
    global _gemini_dernier_echec
    if not getattr(settings, 'GOOGLE_API_KEY', ''):
        return None
    import time
    if time.time() - _gemini_dernier_echec < _GEMINI_COOLDOWN:
        return None  # circuit-breaker : evite de bloquer chaque requete HTTP
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash').generate_content(
            prompt, request_options={'timeout': 8}
        ).text
    except Exception:
        _gemini_dernier_echec = time.time()
        return None


def predire_reussite(scores: list[float], seuil: float = 70.0) -> tuple[float, str]:
    """Probabilite de certification + message (ML si historique, sinon regles)."""
    if len(scores) >= 4 and _SKLEARN_OK:
        try:
            X = [[s] for s in scores]
            y = [1 if s >= seuil else 0 for s in scores]
            if len(set(y)) > 1:
                clf = LogisticRegression().fit(X, y)
                proba = float(clf.predict_proba([[sum(scores) / len(scores)]])[0][1])
                msg = "En bonne voie." if proba >= 0.7 else "Encore des efforts à fournir."
                return round(proba * 100, 1), msg
        except Exception:
            pass
    moyenne = sum(scores) / len(scores) if scores else 0.0
    if moyenne >= seuil + 10:
        return 90.0, "Excellent : demandez votre certification."
    if moyenne >= seuil:
        return 70.0, "En bonne voie : consolidez puis demandez la certification."
    return max(moyenne, 5.0), "Encore des efforts : reprenez les quiz sous le seuil."


def detecter_similarite(reponse: str, autres_reponses: list[str], seuil: float = 0.85) -> bool:
    """Anti-fraude : copie quasi-identique d'une autre reponse (TF-IDF local)."""
    if not _SKLEARN_OK or not reponse.strip() or not autres_reponses:
        return False
    try:
        vec = TfidfVectorizer()
        mat = vec.fit_transform(
            [normalize(reponse)] + [normalize(r) for r in autres_reponses if r.strip()]
        )
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        return bool((sims >= seuil).any())
    except Exception:
        return False


def feedback_certification(reussi: bool, score: float, competence_nom: str) -> str:
    gemini = gemini_generate(
        f"Un apprenant {'obtient' if reussi else 'demande'} la certification "
        f"« {competence_nom} » avec {score:.0f}%. "
        "Rédige un feedback personnalisé motivant en français (4 lignes) "
        "avec 1 recommandation de suite de parcours."
    )
    if gemini:
        return gemini
    if reussi:
        return (
            f"Félicitations ! Certification « {competence_nom} » validée "
            f"avec {score:.0f}%. Ajoutez-la à votre CV et visez la compétence suivante."
        )
    return (
        f"Certification « {competence_nom} » pas encore acquise ({score:.0f}%). "
        "Retravaillez les quiz sous le seuil puis redemandez-la."
    )
