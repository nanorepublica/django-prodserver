import warnings

from django.core.management.commands.runserver import Command as RunServerCommand
from django.utils.deprecation import RemovedAfterNextVersionWarning

class Command(RunServerCommand):
    def handle(self, *args, **kwargs):
        warnings.warn(
            "runserver is deprecated in favor of devserver.",
            RemovedAfterNextVersionWarning,
            stacklevel=2,
        )
        super().handle(*args, **kwargs)
