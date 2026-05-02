import warnings

from .server import Command as ServerCommand

DEPRECATION_MESSAGE = (
    "The `prodserver` management command is deprecated and will be removed in "
    "django-prodserver 4.0.0. Use `python manage.py server` instead."
)


class Command(ServerCommand):
    """Deprecated alias for the `server` management command."""

    def run_from_argv(self, argv: list[str]) -> None:
        """Emit a deprecation notice, then delegate to the `server` command."""
        warnings.warn(DEPRECATION_MESSAGE, DeprecationWarning, stacklevel=2)
        self.stderr.write(
            self.style.WARNING(f"DeprecationWarning: {DEPRECATION_MESSAGE}")
        )
        super().run_from_argv(argv)
