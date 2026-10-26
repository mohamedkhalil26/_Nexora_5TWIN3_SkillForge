# 📋 RAPPORT D'AVANCEMENT — SkillForge (NEXORA, 2026-2027)

> Projet : plateforme web d'apprentissage par compétences — Django 5.2.18 LTS, MVT,
> PostgreSQL 16 (Docker), DRF, IA par module (Gemini optionnel + fallback local).
> Date du rapport : 25/10/2026. État : **application fonctionnelle de bout en bout, testée.**

---

## 1. TÂCHES RÉALISÉES (TOUT CE QUI EST FAIT ET VÉRIFIÉ)

### Sprint 1 — Setup & Configuration ✅ TERMINÉ
- [x] Projet `skillforge` créé (Django 5.2.18, Python 3.10, venv `.venv`)
- [x] `requirements.txt` figé (django, djangorestframework, google-generativeai, scikit-learn, psycopg, reportlab, Pillow…)
- [x] `config/settings.py` : `LANGUAGE_CODE='fr'`, `AUTH_USER_MODEL`, `.env` via python-dotenv, SQLite↔PostgreSQL commutables, DRF `IsAuthenticated` par défaut, durcissement prod (`SECURE_SSL_REDIRECT`, cookies Secure/HttpOnly)
- [x] `.env` / `.env.example` / `.env.pg` / `.env.sqlite.bak`, `.gitignore` (secrets jamais commités)
- [x] 6 apps créées : `accounts`, `learning`, `quizzes`, `mentoring`, `certification`, `dashboard` + `common/text.py`
- [x] `manage.py check` : **0 erreur**

### Sprint 2 — Modèles + IA ✅ TERMINÉ
| App | Modèles | IA (`ai.py` indépendant) |
|---|---|---|
| accounts (Khalil) | `Utilisateur(AbstractUser + role/niveau/objectifs/bio/avatar)` | reco compétences TF-IDF, suggestion bio (Gemini/fallback) |
| learning (Mahdi) | `Competence → Cours → Module → Ressource`, contraintes d'unicité, bons `on_delete` | recherche sémantique, cours similaires, auto-tags, résumé extractif, description + cover (Gemini/HF/fallback) |
| quizzes (Mariem) | `Quiz → Question (QCM/libre) → Tentative → Reponse`, seuils validés | correction QCM + correction sémantique libre, génération QCM, prédiction décrochage, feedback |
| mentoring (Raed) | `MentorProfile → Disponibilite (CheckConstraint fin>début) → Reservation → Message`, visio Jitsi auto | matching score /100, créneaux suggérés, fiche de préparation |
| certification (Malek) | `Certificat (UUID, score, PDF)`, fonction `est_eligible()` | prédiction réussite, anti-fraude similarité, feedback |
| dashboard (Malek) | (pas de modèle, agrégation) | insights langage naturel, `stats_plateforme()` |

- [x] ~3 340 lignes Python (hors migrations), Meta/`__str__`/`get_absolute_url`/validateurs partout

### Sprint 3 — Admin ✅ TERMINÉ
- [x] `ModelAdmin` personnalisé par modèle : `list_display`, `list_filter`, `search_fields`, `ordering`, inlines, `fieldsets`, actions en masse (publier, confirmer, vérifier, régénérer PDF…)
- [x] Groupes métier `Mentors` / `Gestionnaires Catalogue` + permissions (pas de superuser quotidien)
- [x] `seed_demo` : 2 compétences, 1 cours, 1 module, 1 quiz (QCM + libre), mentor vérifié + 3 créneaux, comptes `admin/mentor1/apprenant1` (mdp `demo1234`)

### Sprint 4 — Vues + Templates ✅ TERMINÉ
- [x] `LoginView/LogoutView` (POST), `InscriptionView` (UserCreationForm étendu), `RoleRequiredMixin`
- [x] CRUD générique `List/Detail/Create/Update/DeleteView`, `ModelForm` à champs explicites, `reverse_lazy`, PRG
- [x] 33 templates : `base.html` + `navbar` + `footer`, `extends`/`include`/`{% url %}`, Bootstrap 5, CSRF, visio Jitsi en iframe, boutons IA en `fetch` + `X-CSRFToken`

### Sprint 5 — API REST ✅ TERMINÉ
- [x] 6× `serializers.py` (ModelSerializer, champs explicites), `@api_view` GET/POST/PUT/DELETE
- [x] 15+ endpoints `/api/...` (profils, catalogue, quiz+soumission, dispos/réservations, certificats+éligibilité, résumé)
- [x] Testé : 403 anonyme ✅, 200 connecté ✅ (interface DRF + Postman)

### Sprint 6 — IA + Sécurité + Tests ✅ TERMINÉ
- [x] Pattern workshop AI partout (fonction → vue JsonResponse → bouton fetch), 7 endpoints IA
- [x] Sécurité : PBKDF2, validateurs mdp, permissions par objet (mentor/apprenant/staff), certificats+tenta­tives readonly admin, ORM seul
- [x] Test bout-en-bout `test_flow.py` : **TOUT OK (quiz 90,7 % → réussi)**
- [x] Bugs corrigés : `EnvoyerMessageView` (queryset filtré), JS `cours_detail`, logout POST, `ALLOWED_HOSTS` testserver

### Migration PostgreSQL ✅ TERMINÉE
- [x] Conteneur `skillforge-db` (postgres:16-alpine, `:5432`), 18 tables, seed re-joué, tests re-passés **TOUT OK**
- [x] `docker start skillforge-db` suffit au redémarrage ; retour SQLite possible (`.env.sqlite.bak`)

---

## 2. CE QUI MANQUE / RESTE À FAIRE

### 🔴 Prioritaire (avant la soutenance)
1. [ ] **`tests.py` vides dans les 6 apps** — le cours exige des tests (`startapp` les génère, on ne les a pas écrits). Ajouter au minimum : modèles (contraintes, `est_eligible`), permissions (403/302 anonymes), 1 test d'API par app. `python manage.py test` doit passer.
2. [ ] **Fichiers `static/` vides** — le Ch5 exige `{% load static %}` + CSS/JS/images perso. Ajouter `static/css/style.css` (charte SkillForge) et 1 JS commun au lieu de scripts inline.
3. [ ] **Clés IA réelles** — sans `GOOGLE_API_KEY`, la démo tourne en fallback local (ça marche, mais le jury verra « local »). Obtenir 1 clé gratuite sur ai.google.dev et tester `generer_description` en live. Idem `IMAGEGEN_KEY` (Hugging Face) pour la cover.
4. [ ] **Uploads : whitelist + limite de taille** — actuellement `ImageField/FileField` sans validation d'extension. Ajouter `FileExtensionValidator` + `DATA_UPLOAD_MAX_MEMORY_SIZE`.
5. [ ] **Rate-limit login** — le Ch4 l'exige (anti brute-force). Ajouter `django-axes` ou un verrouillage simple.
6. [ ] **Données de démo enrichies** — 1 seul cours/quiz, c'est léger pour 10 min de démo. Ajouter 2-3 compétences, 2 quiz, 1 certificat déjà délivré, 1 réservation confirmée.

### 🟡 Recommandé (points bonus / robustesse)
7. [ ] **Pagination** (`paginate_by`) sur les listes + `select_related/prefetch_related` vérifiés partout (N+1).
8. [ ] **Page 403/404 personnalisées** + messages d'erreur FR.
9. [ ] **Dates `Disponibilite` futures uniquement** (validateur : pas de créneau passé).
10. [ ] **Anti-fraude branché** : `detecter_similarite()` existe mais n'est jamais appelée lors de la correction — l'appeler dans `PasserQuizView`/`soumettre_quiz`.
11. [ ] **`get_absolute_url()` du `Module`** pointe vers `module-detail` ✅ mais vérifier qu'il est utilisé après création (success_url des CreateView).
12. [ ] **PostgreSQL en soutenance** : prévoir le plan B (SQLite `.env.sqlite.bak`) si Docker refuse de démarrer sur le PC du jury + exporter un dump (`pg_dump`) de secours.
13. [ ] **README équipe** : qui lance quoi (`docker start`, `runserver`), ordre de démo, identifiants — le README actuel est technique, ajouter la fiche « jour J ».
14. [ ] **Git** : le dossier n'est pas un repo (`E:\django project` non versionné). `git init` + premier commit + branches par membre avant de travailler à 5, sinon perte de code garantie.

### 🟢 Optionnel (si temps)
15. [ ] CI minimale (GitHub Actions : `check` + `test`), `collectstatic` + `DEBUG=False` testé une fois en local.
16. [ ] Notifications e-mail (réservation confirmée) via `django.core.mail` en console d'abord.
17. [ ] Internationalisation complète des templates (actuellement FR en dur — suffisant, mais `{% trans %}` = bonus Ch1 « multilingue »).

---

## 3. PLAN D'ACTION PROPOSÉ (par membre)
- **Khalil** : 1 (tests accounts), 5 (rate-limit), 4 (validateurs avatar)
- **Mahdi** : 1 (tests learning), 2 (CSS + covers), 3 (clé Gemini + test description)
- **Mariem** : 1 (tests quizzes), 10 (brancher anti-fraude), 6 (2ᵉ quiz démo)
- **Raed** : 1 (tests mentoring), 9 (validateur dates), 6 (réservation confirmée démo)
- **Malek** : 1 (tests certification/dashboard), 8 (403/404), 7 (pagination), 12 (dump PG + plan B), 14 (git init + branches)

**Ordre : 14 (git) → 1 (tests) → 4/5/9/10 (sécurité) → 2/6 (démo) → 3 (clés) → 12/13 (jour J).**
