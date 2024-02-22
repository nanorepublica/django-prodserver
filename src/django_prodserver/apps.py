"""App configuration."""

from django.apps import AppConfig


class DjangoProdserverConfig(AppConfig):
    """App configuration for django-prodserver."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_prodserver"
