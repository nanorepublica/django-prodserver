"""Settings to be used for tests."""

from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-1uhn#!v$y#jmy)%mp03n%ao(c}7qa6h33Fw6n5qtk-@o_1^@z-"  # nosec

# Application definition

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "src.django_prodserver.apps.DjangoProdserverConfig",
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

USE_TZ = True
DEBUG = True
ROOT_URLCONF = "src.django_prodserver.urls"
