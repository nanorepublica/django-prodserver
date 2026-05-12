"""Deprecated; see ``django_prodserver.backends.dev.django_runserver``."""

import warnings

from .dev.django_runserver import DjangoRunserver

warnings.warn(
    "django_prodserver.backends.django_runserver is deprecated; import from "
    "django_prodserver.backends.dev.django_runserver instead. This module will "
    "be removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DjangoRunserver"]
