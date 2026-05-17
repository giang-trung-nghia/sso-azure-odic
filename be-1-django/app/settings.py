"""
Django settings for `be-1-django`.

Infra: PostgreSQL + Redis-backed sessions.
Auth: optional Microsoft Entra ID OIDC via mozilla-django-oidc (see `OIDC_ENABLED`).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = _csv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,be-1-django")

# --- Microsoft Entra ID (Azure AD) OIDC ---
AZURE_AD_TENANT_ID = os.environ.get("AZURE_AD_TENANT_ID", "").strip()
AZURE_AD_CLIENT_ID = os.environ.get("AZURE_AD_CLIENT_ID", "").strip()
AZURE_AD_CLIENT_SECRET = os.environ.get("AZURE_AD_CLIENT_SECRET", "").strip()
OIDC_ENABLED = bool(AZURE_AD_TENANT_ID and AZURE_AD_CLIENT_ID and AZURE_AD_CLIENT_SECRET)

_INSTALLED_CORE = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
]

INSTALLED_APPS = list(_INSTALLED_CORE)
if OIDC_ENABLED:
    INSTALLED_APPS += ["mozilla_django_oidc"]
INSTALLED_APPS += ["accounts"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]
if OIDC_ENABLED:
    # Periodically re-checks Entra id_token validity (see mozilla-django-oidc docs).
    MIDDLEWARE += ["mozilla_django_oidc.middleware.SessionRefresh"]
MIDDLEWARE += [
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "app.wsgi.application"


# --- Database (PostgreSQL when POSTGRES_HOST is set; else SQLite for bare-metal local) ---
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "").strip()
if POSTGRES_HOST:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "sso_learning"),
            "USER": os.environ.get("POSTGRES_USER", "sso"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": POSTGRES_HOST,
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"


# --- Redis cache + session storage (when REDIS_HOST is set) ---
REDIS_HOST = os.environ.get("REDIS_HOST", "").strip()
REDIS_PORT = os.environ.get("REDIS_PORT", "6379").strip()

if REDIS_HOST:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.db"


# --- CORS (browser clients for fe-1 → be-1-django) ---
_cors = _csv("DJANGO_CORS_ORIGINS", "")
if _cors:
    CORS_ALLOWED_ORIGINS = _cors
    CORS_ALLOW_CREDENTIALS = True
    CSRF_TRUSTED_ORIGINS = _cors


# --- Django auth / login redirects ---
if OIDC_ENABLED:
    AUTHENTICATION_BACKENDS = (
        "accounts.backends.EntraOIDCAuthenticationBackend",
        "django.contrib.auth.backends.ModelBackend",
    )
else:
    AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/me/"
LOGIN_REDIRECT_URL_FAILURE = "/accounts/login/?error=1"
LOGOUT_REDIRECT_URL = os.environ.get(
    "DJANGO_LOGOUT_REDIRECT_URL",
    "http://127.0.0.1:5171/",
)

# Where Entra should send the browser after `/oauth2/v2.0/logout` (must be registered in Entra if required).
ENTRA_POST_LOGOUT_REDIRECT_URI = os.environ.get("ENTRA_POST_LOGOUT_REDIRECT_URI", "").strip()

# mozilla-django-oidc: allow GET /oidc/logout/ for simple local testing (prefer POST in production).
ALLOW_LOGOUT_GET_METHOD = os.environ.get("DJANGO_ALLOW_LOGOUT_GET", "1") == "1"

# Safe `next=` targets for /oidc/authenticate/?next=...
OIDC_REDIRECT_ALLOWED_HOSTS = _csv(
    "OIDC_REDIRECT_ALLOWED_HOSTS",
    "127.0.0.1,127.0.0.1:5171,localhost,localhost:5171",
)


if OIDC_ENABLED:
    OIDC_RP_CLIENT_ID = AZURE_AD_CLIENT_ID
    OIDC_RP_CLIENT_SECRET = AZURE_AD_CLIENT_SECRET

    OIDC_RP_SIGN_ALGO = "RS256"
    OIDC_OP_JWKS_ENDPOINT = (
        f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/discovery/v2.0/keys"
    )
    OIDC_OP_AUTHORIZATION_ENDPOINT = (
        f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/oauth2/v2.0/authorize"
    )
    OIDC_OP_TOKEN_ENDPOINT = (
        f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/oauth2/v2.0/token"
    )
    OIDC_OP_USER_ENDPOINT = "https://graph.microsoft.com/oidc/userinfo"

    OIDC_RP_SCOPES = os.environ.get(
        "OIDC_RP_SCOPES",
        "openid email profile offline_access",
    )

    OIDC_USE_NONCE = True
    OIDC_USE_PKCE = os.environ.get("OIDC_USE_PKCE", "1") == "1"

    OIDC_OP_LOGOUT_URL_METHOD = "accounts.oidc.provider_logout_url"

    # Optional token storage (useful when you later call Microsoft Graph APIs).
    OIDC_STORE_ACCESS_TOKEN = os.environ.get("OIDC_STORE_ACCESS_TOKEN", "0") == "1"
    OIDC_STORE_ID_TOKEN = os.environ.get("OIDC_STORE_ID_TOKEN", "0") == "1"

    OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = int(
        os.environ.get("OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS", str(60 * 15))
    )

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "loggers": {
            "mozilla_django_oidc": {
                "handlers": ["console"],
                "level": os.environ.get("OIDC_LOG_LEVEL", "INFO"),
            },
        },
    }

else:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {"class": "logging.StreamHandler"},
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
