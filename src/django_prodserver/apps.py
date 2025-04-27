from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProdserverAppConfig(AppConfig):
    """App config for Django prodserver."""

    name = "django_prodserver"
    verbose_name = _("prodserver")
