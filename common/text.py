"""Outils texte partages (PAS un service IA) — Ch2/Ch5 : factorisation DRY.

Chaque app garde son propre `ai.py` independant (exigence prof).
Ce module ne fait que du nettoyage/normalisation, sans decision metier.
"""
import re
import unicodedata


def normalize(text: str) -> str:
    """Minuscules, sans accents, espaces propres — base commune TF-IDF."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def keywords(text: str, limit: int = 8) -> list[str]:
    """Mots-cles frequentiels simples (stop-words FR minimaux)."""
    stop = {
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "ou",
        "pour", "avec", "dans", "sur", "est", "sont", "que", "qui",
        "aux", "ces", "son", "sa", "ses", "au", "en", "par", "plus",
        "pas", "comme", "tout", "tous", "etre", "avoir", "vous",
        "nous", "ils", "elles", "the", "and", "vos", "votre",
    }
    words = [w for w in normalize(text).split() if len(w) > 2 and w not in stop]
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=freq.get, reverse=True)[:limit]
