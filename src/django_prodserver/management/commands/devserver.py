from django.core.management.commands.runserver import Command as RunServerCommand


class Command(RunServerCommand):
    """Class to override the name of 'runserver'."""

    pass
