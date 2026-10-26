"""IA learning (INDEPENDANTE) — Mahdi : recherche semantique, resume, tags, description+cover."""
from django.conf import settings

from common.text import keywords, normalize

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
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


def recherche_semantique(requete: str, cours: list, top: int = 5) -> list:
    """TF-IDF local : 'je veux creer un site' -> bons cours sans mot exact."""
    if not requete or not cours:
        return list(cours)[:top]
    if not _SKLEARN_OK:
        q = normalize(requete)
        return [c for c in cours if q and q in normalize(f"{c.titre} {c.description}")][:top] or list(cours)[:top]
    try:
        docs = [f"{c.titre} {c.description}" for c in cours]
        vec = TfidfVectorizer()
        mat = vec.fit_transform([normalize(requete)] + [normalize(d) for d in docs])
        sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
        return [c for c, _ in sorted(zip(cours, sims), key=lambda x: x[1], reverse=True)[:top]]
    except Exception:
        return list(cours)[:top]


def cours_similaires(cours_cible, tous_les_cours: list, top: int = 3) -> list:
    """Cours de la meme competence les plus proches textuellement."""
    candidats = [c for c in tous_les_cours if c.pk != cours_cible.pk]
    texte = f"{cours_cible.titre} {cours_cible.description}"
    return [c for c in recherche_semantique(texte, candidats, top=top)]


def auto_tags(titre: str, description: str) -> list[str]:
    return keywords(f"{titre} {description}", limit=6)


def resumer_module(contenu: str, phrases: int = 3) -> str:
    """Resume extractif : top phrases par frequence (100% local, offline)."""
    import re

    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", contenu or "") if len(p.strip()) > 20]
    if len(parts) <= phrases:
        return contenu
    scores = {}
    for i, p in enumerate(parts):
        mots = [m for m in normalize(p).split() if len(m) > 3]
        scores[i] = len(set(mots)) + (len(parts) - i) * 0.05  # bonus debut
    top_idx = sorted(sorted(scores, key=scores.get, reverse=True)[:phrases])
    return " ".join(parts[i] for i in top_idx)


def generer_image_cover(titre: str) -> tuple[bytes | None, str]:
    """Workshop AI partie 2 : cover via Pollinations.ai (gratuit, sans cle).

    Retourne (bytes, ""). En cas d'echec reseau : (None, "network: ...").
    NOTE : HF Inference ne sert plus de modeles image gratuits (410/400);
    Pollinations reste le seul generateur sans cle. La cle IMAGEGEN_KEY
    reste supportee si HF reactive un provider (voir docstring historique).
    """
    import logging
    import urllib.parse

    log = logging.getLogger(__name__)
    try:
        import requests
    except ImportError:
        return None, "requests_not_installed"
    prompt = urllib.parse.quote(f"online course cover illustration, flat design, no text, theme: {titre}")
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=576&nologo=true"
    try:
        resp = requests.get(url, timeout=120)
    except Exception as e:  # DNS, proxy, timeout reseau...
        err = f"network: {type(e).__name__}"
        log.warning("Cover IA : %s", err)
        return None, err
    ctype = resp.headers.get("content-type", "")
    if resp.status_code == 200 and resp.content and "image" in ctype:
        return resp.content, ""
    err = f"{resp.status_code} {resp.content[:200]!r}"
    log.warning("Cover IA : %s", err)
    return None, err


def generer_description(titre: str) -> str:
    """Workshop AI : Gemini d'abord, fallback local sinon."""
    gemini = gemini_generate(
        f"Rédige en 4 lignes une description de cours motivante pour : {titre}. En français."
    )
    if gemini:
        return gemini
    return (
        f"Ce cours « {titre} » vous guide pas à pas, de la découverte "
        "aux mises en pratique. Modules progressifs, ressources variées et quiz "
        "pour valider chaque étape avant la certification."
    )
