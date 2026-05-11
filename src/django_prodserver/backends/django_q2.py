"""Deprecated; see ``django_prodserver.backends.workers.django_q2``."""

import warnings

from .workers.django_q2 import DjangoQ2Worker

warnings.warn(
    "django_prodserver.backends.django_q2 is deprecated; import from "
    "django_prodserver.backends.workers.django_q2 instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DjangoQ2Worker"]
