from __future__ import annotations

SECRET_KEY = "NOTASECRET"  # noqa S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}
DEBUG = True
STATIC_URL = "static/"
STATIC_ROOT = "static"
USE_TZ = True
TIME_ZONE = "UTC"
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_prodserver",
    "tests.testapp",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

PRODUCTION_PROCESSES = {
    "web-g": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8222", "workers": "2"},
    },
    "web-w": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {},
    },
    "web-u": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {},
    },
    "web-uw": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornWSGIServer",
        "ARGS": {},
    },
    "worker-celery": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "tests.celery.app",
        "ARGS": {"loglevel": "info"},
    },
    "beat-celery": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "tests.celery.app",
        "ARGS": {"loglevel": "info"},
    },
    "flower": {
        "BACKEND": "django_prodserver.backends.celery.CeleryFlower",
        "APP": "tests.celery.app",
        "ARGS": {"port": "5555", "address": "0.0.0.0"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {},
    },
    "dev": {
        "BACKEND": "django_prodserver.backends.django_runserver.DjangoRunserver",
        "ARGS": {"addrport": "0.0.0.0:9000"},
    },
    "dev-asgi": {
        "BACKEND": "django_prodserver.backends.daphne.DaphneRunserver",
        "ARGS": {"addrport": "0.0.0.0:9000"},
    },
    "dev-werkzeug": {
        "BACKEND": "django_prodserver.backends.werkzeug.WerkzeugRunserver",
        "ARGS": {"addrport": "0.0.0.0:9000"},
    },
}


TASKS = {"default": {"BACKEND": "django_tasks.backends.database.DatabaseBackend"}}

WSGI_APPLICATION = "tests.wsgi.application"
ASGI_APPLICATION = "tests.asgi.application"
