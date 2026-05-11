"""Deprecated; see ``django_prodserver.backends.workers.celery``."""

import warnings

from .workers.celery import CeleryBeat, CeleryFlower, CeleryWorker

warnings.warn(
    "django_prodserver.backends.celery is deprecated; import from "
    "django_prodserver.backends.workers.celery instead. This module will be "
    "removed in django-prodserver 4.0.0.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["CeleryBeat", "CeleryFlower", "CeleryWorker"]
