import warnings
from typing import Any

from django.core.management.commands.runserver import Command as RunServerCommand

DEPRECATION_MESSAGE = (
    "The `devserver` management command is deprecated and will be removed in "
    "django-prodserver 4.0.0. Use `python manage.py server` instead."
)


class Command(RunServerCommand):
    """Class to override the name of 'runserver'."""

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """Override this to provide the deprecation message."""
        warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        self.stderr.write(
            self.style.WARNING(f"DeprecationWarning: {DEPRECATION_MESSAGE}")
        )
        super().handle(*args, **kwargs)
