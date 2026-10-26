"""Configuration SkillForge — Django 5.2 (Ch1 : settings.py centralise tout)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")  # Workshop AI : cles API + secrets dans .env


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in ("1", "true", "oui", "yes")


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver").split(",")

# ---- Applications : projet = plusieurs apps reutilisables (Ch1) ----
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",  # Workshop API REST : DRF
    "axes",  # Tache prio #5 : rate-limit login anti brute-force (Ch4)
    "accounts",  # Khalil : utilisateurs, auth, profils
    "learning",  # Mahdi : competences, cours, ressources
    "quizzes",  # Mariem : progression, quiz, evaluations
    "mentoring",  # Raed : mentorat, disponibilites, reservations
    "certification",  # Malek : certification (PDF)
    "dashboard",  # Malek : tableaux de bord + stats
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",  # Tache prio #5 : doit etre en dernier
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---- Templates DTL (Ch5) ----
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---- Base de donnees (Ch2) : SQLite en dev, PostgreSQL si variables definies ----
if os.getenv("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "USER": os.getenv("POSTGRES_USER", ""),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---- Auth (Ch4) : modele User personnalise declare DES LE DEBUT ----
AUTH_USER_MODEL = "accounts.Utilisateur"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",  # Tache prio #5 : rate-limit d'abord
    "django.contrib.auth.backends.ModelBackend",
]

# django-axes : verrouille apres 5 echecs, 1h de gel (Ch4 anti brute-force)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # heures
AXES_LOCKOUT_TEMPLATE = "accounts/verrouille.html"

# Uploads (Ch4) : plafonds globaux en complement des validateurs par champ
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "home"

# Hachage PBKDF2 par defaut (870k iterations depuis Django 5.1) + validateurs (Ch4)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---- API REST (workshop) : authentification requise par defaut ----
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

LANGUAGE_CODE = "fr"  # Ch3 : interface admin en francais
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- IA : cles optionnelles (workshop AI). Absentes => fallbacks 100% locaux ----
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
IMAGEGEN_KEY = os.getenv("IMAGEGEN_KEY", "")

# ---- Securite prod (Ch4 : bonnes pratiques) ----
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
