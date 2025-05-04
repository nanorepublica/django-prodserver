"""
These are the available settings.

All attributes prefixed ``PRODUCTION_*`` can be overridden from your Django
project's settings module by defining a setting with the same name.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings as django_settings

# All attributes accessed with this prefix are possible to overwrite
# through django.conf.settings.
SETTINGS_PREFIX = "PRODUCTION_"


@dataclass(frozen=True)
class AppSettings:
    """Access this instance as `.conf.app_settings`."""

    PRODUCTION_PROCESSES: Mapping[str, Mapping[str, str]] = field(default_factory=dict)
    """Whether the app is enabled (dummy setting to demo usage)."""

    def __getattribute__(self, __name: str) -> Any:
        """
        Check if a Django project settings should override the app default.

        In order to avoid returning any random properties of the django settings,
        we inspect the prefix firstly.
        """
        if __name.startswith(SETTINGS_PREFIX) and hasattr(django_settings, __name):
            return getattr(django_settings, __name)

        return super().__getattribute__(__name)


app_settings = AppSettings()
