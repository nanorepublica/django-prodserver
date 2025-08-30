from typing import Any

from django.core import management
from django.core.exceptions import ImproperlyConfigured

from .base import BaseServerBackend


class DjangoQ2Worker(BaseServerBackend):
    """Backend to start a Django-Q2 task queue worker."""

    def __init__(self, **server_args: Any) -> None:
        """
        Initialize the Django-Q2 worker backend.

        Validates that django-q2 is properly installed and configured.

        Raises:
            ImproperlyConfigured: If django-q2 is not installed or
                                if 'django_q' is not in INSTALLED_APPS.

        """
        # Check if django-q2 is installed
        try:
            import django_q  # noqa: F401
        except ImportError as e:
            raise ImproperlyConfigured(
                "django-q2 is required to use DjangoQ2Worker backend. "
                "Install it with: pip install django-q2"
            ) from e

        # Verify django_q is in INSTALLED_APPS
        from django.conf import settings

        if "django_q" not in settings.INSTALLED_APPS:
            raise ImproperlyConfigured(
                "Add 'django_q' to INSTALLED_APPS to use DjangoQ2Worker backend. "
                "See https://django-q2.readthedocs.io/en/master/install.html "
                "for setup instructions."
            )

        super().__init__(**server_args)

    def start_server(self, *args: str) -> None:
        """
        Start Django-Q2 cluster using qcluster management command.

        Args:
            *args: Command line arguments to pass to the qcluster command.
                  Common arguments include:
                  - --verbosity: Control logging verbosity (0-3)
                  - --cluster-name: Specify cluster name
                  - --settings: Override Django settings module

        """
        management.call_command("qcluster", *args)

    def prep_server_args(self) -> list[str]:
        """
        Prepare arguments for qcluster command.

        Returns:
            List of formatted command line arguments for qcluster.

        Note:
            Most Django-Q2 configuration should be done through the Q_CLUSTER
            setting in Django settings. The ARGS configuration in
            PRODUCTION_PROCESSES is primarily for runtime options like
            verbosity and cluster naming.

        """
        return super().prep_server_args()
