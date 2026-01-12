"""
Django settings for riseup project.
"""

from pathlib import Path
from datetime import timedelta
import os
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_dotenv(path):
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

SECRET_KEY = 'django-insecure-p=4%n$c&-mzp6k)2$=#0ug16-=e)e2$g2efysdy1$7n@0g@wko'


DEBUG = False
ALLOWED_HOSTS = [
    "api.riseuply.uz",
    ".railway.app"
]  

# ==========================================================
#  DJANGO APPS
# ==========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    # Local apps
    'core.apps.CoreConfig',
]

# ==========================================================
#  MIDDLEWARE
# ==========================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.DailyBonusMiddleware",
]


ROOT_URLCONF = 'riseup.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'riseup.wsgi.application'

# ==========================================================
#  DATABASE
# ==========================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres.icuveokuqwhfcbvsrdlj",
        "PASSWORD": "Riseup_2025",
        "HOST": "aws-1-eu-west-1.pooler.supabase.com",
        "PORT": "5432",


        "CONN_MAX_AGE": 300,  # 5 daqiqa (hatto 600 ham bo‘ladi)

        "OPTIONS": {
            "sslmode": "require",
            "connect_timeout": 5,  # tez fail bo‘lsin
        },
    }
}


# ==========================================================
#  PASSWORD VALIDATORS
# ==========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================================
#  LANGUAGE / TIMEZONE
# ==========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# ==========================================================
#  STATIC FILES
# ==========================================================
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================================
#  DJANGO REST FRAMEWORK
# ==========================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# ==========================================================
#  CORS (Frontend bilan aloqa uchun)
# ==========================================================
CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://riseuply.vercel.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://riseuply.vercel.app",
]


# yoki xavfsiz variant (agar front 5500 portda ishlasa)
# CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5500"]

# ==========================================================
#  SIMPLE JWT CONFIG (Token muddati)
# ==========================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

USE_TZ = True
TIME_ZONE = "Asia/Tashkent"
