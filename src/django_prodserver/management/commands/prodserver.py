import sys
from argparse import ArgumentParser
from collections.abc import Mapping

from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError
from django.utils.module_loading import import_string

from ...conf import app_settings


class Command(BaseCommand):
    """The main prodserver command."""

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Add arguments."""
        try:
            choices = app_settings.PRODUCTION_PROCESSES.keys()
        except AttributeError:
            raise CommandError(
                "PRODUCTION_PROCESSES setting has been configured incorrectly.\n"
                "Check the documentation to configure this setting correctly."
            ) from None
        try:
            default = next(iter(choices))
        except StopIteration:
            raise CommandError(
                "No servers configured in the PRODUCTION_PROCESSES setting.\n"
                "Configure your servers before running this command."
            ) from None
        parser.add_argument(
            "server_name",
            type=str,
            choices=choices,
            nargs="?",
            default=default,
        )
        parser.add_argument("--list", action="store_true")

    def run_from_argv(self, argv: list[str]) -> None:
        """
        Slight modification of the BaseCommand function.

        Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options = parser.parse_args(argv[2:])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop("args", ())
        handle_default_options(options)

        if cmd_options["list"]:
            self.list_process_names()
            return

        try:
            self.start_server(*args, **cmd_options)
        except CommandError as e:
            if options.traceback:
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write(f"{e.__class__.__name__}: {e}")
            sys.exit(e.returncode)

    def start_server(
        self, server_name: str, *args: list[str], **kwargs: Mapping[str, str]
    ) -> None:
        """Start the correct process based on the provided name."""
        # this try/except could be removed, keeping for now as it's a nicer
        try:
            server_config = app_settings.PRODUCTION_PROCESSES[server_name]
        except KeyError:
            available_servers = "\n ".join(app_settings.PRODUCTION_PROCESSES.keys())
            raise CommandError(
                f"Server named '{server_name}' not found in the PRODUCTION_PROCESSES"
                f" setting\nAvailable names are:\n {available_servers}"
            ) from None

        self.stdout.write(self.style.NOTICE(f"Starting server named {server_name}"))

        try:
            server_backend = server_config["BACKEND"]
        except KeyError:
            raise CommandError(
                f"Backend not configured for server named {server_name}"
            ) from None

        backend_class = import_string(server_backend)

        backend = backend_class(**server_config)
        backend.start_server(*backend.prep_server_args())

    def list_process_names(self) -> None:
        """Simple function to return a list of the configured processes."""
        available_servers = "\n ".join(app_settings.PRODUCTION_PROCESSES.keys())
        self.stdout.write(
            self.style.SUCCESS(
                f"Available production process names are:\n {available_servers}"
            )
        )
