# SkillForge — Learn. Practice. Connect. Get Certified.

Plateforme web d'apprentissage par compétences (Django 5.2 LTS, MVT, PostgreSQL/SQLite).
Équipe NEXORA — 2026-2027.

## Parcours
Choisir une compétence → Apprendre → Pratiquer → Être accompagné → Être évalué → Être certifié.

## Prérequis
- Python 3.10+
- (optionnel) PostgreSQL pour la soutenance, clés `GOOGLE_API_KEY` / `IMAGEGEN_KEY`

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # puis remplir SECRET_KEY (+ clés IA, DB)
python manage.py migrate
python manage.py seed_demo    # comptes demo, mot de passe : demo1234
python manage.py createsuperuser
python manage.py runserver
```

## Comptes démo (mot de passe : `demo1234`)
| Compte | Rôle |
|---|---|
| `admin` | superuser / back-office |
| `mentor1` | mentor vérifié |
| `apprenant1` | apprenant |

## Structure
| App | Responsable | Contenu |
|---|---|---|
| `accounts` | Khalil | `Utilisateur(AbstractUser+role)`, register/login/logout, `ai.py` (reco + bio) |
| `learning` | Mahdi | `Competence→Cours→Module→Ressource`, recherche sémantique, `ai.py` (resume, tags, description+cover) |
| `quizzes` | Mariem | `Quiz→Question(QCM/libre)→Tentative/Reponse`, correction IA, `ai.py` (génération QCM, décrochage) |
| `mentoring` | Raed | `MentorProfile→Disponibilite→Reservation→Message`, visio Jitsi, `ai.py` (matching, créneaux, fiche) |
| `certification` | Malek | `Certificat` + PDF reportlab, `ai.py` (prédiction, anti-fraude) |
| `dashboard` | Malek | home par rôle, stats, `ai.py` (insights) |
| `common` | partagé | `text.py` (normalisation TF-IDF — pas un service IA) |

## API REST (`/api/...`, DRF)
- `/api/comptes/profil/` `apprenants/` `suggerer-bio/`
- `/api/apprendre/competences/` `cours/` `cours/<slug>/` `generer-description/` `generer-image/`
- `/api/quiz/` `<pk>/` `<pk>/soumettre/` `mes-tentatives/` `generer-questions/`
- `/api/mentorat/mentors/` `disponibilites/` `reservations/` `.../annuler/` `fiche-preparation/`
- `/api/certificats/` `eligibilite/<slug>/` `demander/<slug>/`
- `/api/dashboard/resume/`

Tester via l'interface DRF (`/api/...` dans le navigateur, connecté) ou Postman.

## IA (1 module indépendant par app, offline par défaut)
Chaque app a son `ai.py` : Gemini si `GOOGLE_API_KEY` définie, sinon fallback
100 % local (`scikit-learn`, TF-IDF/similarité cosinus). Images via Hugging Face
si `IMAGEGEN_KEY` définie, sinon erreur 503 propre. Rien ne plante sans clés.

## Sécurité
- `SECRET_KEY` + clés dans `.env` (jamais commité, voir `.gitignore`)
- `AbstractUser` + `role`, PBKDF2, validateurs, `LoginRequired` / `RoleRequired` / permissions par objet
- CSRF partout (`{% csrf_token %}` + header `X-CSRFToken` dans les `fetch`)
- ORM uniquement, `fields=[...]` explicites (forms + serializers), validateurs modèles
- Admin : groupes `Mentors` / `Gestionnaires Catalogue`, certificats/tentatives en lecture seule
- Prod : `DEBUG=False` → HTTPS forcé, cookies `Secure`, `SESSION_COOKIE_HTTPONLY`

## Soutenance (scénario 10 min)
1. Landing → inscription (bio IA) → reco compétences
2. Recherche « je veux créer un site » → cours → module (résumé/tags IA)
3. Passer le quiz démo → 90% → feedback IA
4. Réserver un créneau mentor (fiche IA) → confirmer → visio Jitsi
5. Demander le certificat → PDF téléchargeable
6. Dashboards (apprenant/mentor/admin) + API DRF + `/admin/` en français
