"""IA quizzes (INDEPENDANTE) — Mariem : correction semantique, generation QCM, decrochage.
Le 'vrai LLM' du projet : Gemini si cle, sinon TF-IDF local (offline, soutenance-proof).
"""
from django.conf import settings

from common.text import keywords, normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
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


def corriger_qcm(question, reponse_donnee: str) -> tuple[bool, float]:
    """QCM : compare le n° choisi au n° attendu. Retourne (correct, points)."""
    try:
        attendu = int(str(question.bonne_reponse).strip())
        donne = int(str(reponse_donnee).strip())
        ok = attendu == donne
        return ok, float(question.points) if ok else 0.0
    except (ValueError, TypeError):
        return False, 0.0


def corriger_libre(question, reponse_donnee: str) -> tuple[bool, float, str]:
    """Reponse libre : similarite cosinus vs reponse attendue + feedback."""
    attendu = question.bonne_reponse or ""
    if not reponse_donnee.strip():
        return False, 0.0, "Réponse vide : relisez le module puis réessayez."
    gemini = gemini_generate(
        "Tu es un correcteur bienveillant. Question : "
        f"{question.enonce}\nRéponse attendue : {attendu}\n"
        f"Réponse de l'apprenant : {reponse_donnee}\n"
        "Donne une note sur 1 (nombre seul en première ligne) puis un feedback "
        "personnalisé en français en 3 lignes."
    )
    if gemini:
        try:
            note = float(gemini.splitlines()[0].strip().replace(",", "."))
            note = max(0.0, min(1.0, note))
        except (ValueError, IndexError):
            note = 0.5
        feedback = "\n".join(gemini.splitlines()[1:]).strip() or gemini
        return note >= 0.6, note * question.points, feedback
    # Fallback local (offline) : similarite TF-IDF
    if not _SKLEARN_OK:
        ok = normalize(reponse_donnee) == normalize(attendu)
        return ok, float(question.points) if ok else 0.0, feedback_local(ok)
    try:
        vec = TfidfVectorizer()
        mat = vec.fit_transform([normalize(attendu), normalize(reponse_donnee)])
        sim = float(cosine_similarity(mat[0:1], mat[1:])[0][0])
    except Exception:
        sim = 0.0
    note = sim
    return note >= 0.6, round(note * question.points, 2), feedback_local(note >= 0.6, sim)


def feedback_local(reussi: bool, sim: float = 0.0) -> str:
    if reussi:
        return f"Bonne réponse (similarité {sim:.0%}). Continuez ainsi."
    return (
        f"Réponse incomplète (similarité {sim:.0%}). "
        "Reprenez les mots-clés du module et reformulez avec vos propres mots."
    )


def generer_qcm(contenu: str, nb: int = 3) -> list[dict]:
    """Generation auto de QCM depuis un contenu (Gemini si cle, sinon extractif local)."""
    gemini = gemini_generate(
        "Génère "
        f"{nb} QCM en français depuis ce contenu. Format par QCM : "
        "question | choix1 ; choix2 ; choix3 | numéro bonne réponse.\nContenu : "
        f"{contenu[:2000]}"
    )
    if gemini:
        out = []
        for line in gemini.splitlines():
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    out.append(
                        {"enonce": parts[0], "choix": parts[1], "bonne_reponse": parts[2]}
                    )
        if out:
            return out[:nb]
    # Fallback local : QCM "quel mot-clé manque" a partir des top mots
    mots = keywords(contenu, limit=max(nb * 2, 4))
    return [
        {
            "enonce": f"Lequel de ces termes est central dans ce module ?",
            "choix": " ; ".join((mots[i : i + 3] + ["élément"])[0:3]),
            "bonne_reponse": "1",
        }
        for i in range(0, min(nb * 2, len(mots)), 2)
    ][:nb]


def predire_risque(scores: list[float]) -> str:
    """Decrochage : regression logistique si assez d'historique, sinon regles.
    Retourne 'stable' | 'a_risque' | 'excellent'."""
    if len(scores) >= 6 and _SKLEARN_OK:
        try:
            X = [[s] for s in scores[:-1]]
            y = [1 if s >= 70 else 0 for s in scores[1:]]
            if len(set(y)) > 1:
                clf = LogisticRegression().fit(X, y)
                proba = clf.predict_proba([[scores[-1]]])[0][1]
                if proba >= 0.8:
                    return "excellent"
                return "stable" if proba >= 0.4 else "a_risque"
        except Exception:
            pass
    dernier = scores[-1] if scores else 0
    if dernier >= 85:
        return "excellent"
    if dernier >= 50:
        return "stable"
    return "a_risque"


def feedback_quiz(reussi: bool, score: float, points_faibles: str = "") -> str:
    gemini = gemini_generate(
        f"Un apprenant a obtenu {score:.0f}% à un quiz ({'réussi' if reussi else 'non réussi'}). "
        f"Points faibles : {points_faibles or 'aucun détail'}. "
        "Donne un feedback personnalisé motivant en français (4 lignes max) avec 1 recommandation."
    )
    if gemini:
        return gemini
    if reussi:
        return (
            f"Bravo, {score:.0f}% ! Objectif atteint. "
            "Consolidez en passant au module suivant."
        )
    return (
        f"Score de {score:.0f}%, sous le seuil. "
        f"Reprenez : {points_faibles or 'les modules du cours'}, "
        "puis retentez le quiz."
    )
