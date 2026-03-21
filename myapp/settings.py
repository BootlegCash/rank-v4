import os
from pathlib import Path
import dj_database_url
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')  # change on production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ✅ Add your render URL and localhost
ALLOWED_HOSTS = [
    "afterhoursranked.com",
    "www.afterhoursranked.com",
    "ranked-0xtx.onrender.com",
    "127.0.0.1",
    "localhost",
]

# ----------------- INSTALLED APPS -----------------
INSTALLED_APPS = [
    'jazzmin', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
     # if you installed django-jazzmin
    'rest_framework_simplejwt',

    # Your apps
    'accounts',
    'achievements',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files on Render
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'myapp.wsgi.application'

# ----------------- DATABASE -----------------
# ✅ Use DATABASE_URL on Render, fallback to SQLite locally
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ----------------- PASSWORD VALIDATION -----------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------- INTERNATIONALIZATION -----------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------- STATIC & MEDIA -----------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ✅ Fix warning: only include STATICFILES_DIRS if folder exists
_static_dir = BASE_DIR / 'static'
if _static_dir.exists():
    STATICFILES_DIRS = [ _static_dir ]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------- REST FRAMEWORK -----------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'Default_Authentication_Classes': [
        'rest_framework.authenticatiion.TokenAuthentication',]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ----------------- CORS -----------------
CORS_ALLOW_ALL_ORIGINS = True


# ----------------- LOGGING (optional debug) -----------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# Email (SendGrid)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = "no-reply@rankeddrinking.com"
SERVER_EMAIL = "no-reply@rankeddrinking.com"

# Helps Django build absolute links in emails in some cases
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "127.0.0.1:8000")


# Render / reverse proxy HTTPS fix
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

CSRF_TRUSTED_ORIGINS = [
    "https://ranked-0xtx.onrender.com",
     "https://afterhoursranked.com",
    "https://www.afterhoursranked.com",
]

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
}

JAZZMIN_SETTINGS = {
    "site_title": "After Hours Admin",
    "site_header": "After Hours",
    "site_brand": "After Hours Ranked",

    "icons": {
        "accounts.Profile": "fas fa-user",
        "auth.User": "fas fa-users",
        "auth.Group": "fas fa-user-shield",
        "achievements.Achievement": "fas fa-trophy",
    },

    "order_with_respect_to": [
        "accounts",
        "achievements",
        "auth",
    ],

    "custom_links": {
        "accounts": [{
            "name": "📊 Stats Dashboard",
            "url": "admin:accounts_profile_stats",
            "icon": "fas fa-chart-bar",
        }]
    }
}


JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",   # 🔥 best for your neon vibe
}