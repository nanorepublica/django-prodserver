from __future__ import annotations

SECRET_KEY = "NOTASECRET"  # noqa S105

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    },
}

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
        "APP": "example_project.celery.app",
        "ARGS": {},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {},
    },
}


TASKS = {"default": {"BACKEND": "django_tasks.backends.database.DatabaseBackend"}}

WSGI_APPLICATION = "tests.wsgi.application"
ASGI_APPLICATION = "tests.asgi.application"
