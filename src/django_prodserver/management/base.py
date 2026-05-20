import sys
from argparse import ArgumentParser
from collections.abc import Mapping

from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError
from django.utils.module_loading import import_string

from ..backends.base import (
    BaseProcessBackend,
    BaseServerBackend,
    BaseWorkerBackend,
)
from ..conf import app_settings


class BaseProcessCommand(BaseCommand):
    """
    Shared implementation behind the ``server`` and ``worker`` commands.

    Subclasses select which kind of process they manage by setting
    :attr:`process_label` (used in user-facing messages) and
    :attr:`backend_base_class` (the base class a configured backend must
    subclass to be runnable by the command).
    """

    #: Human readable noun for the kind of process managed (e.g. ``"server"``).
    process_label: str = "process"
    #: Backends configured for this command must subclass this class.
    backend_base_class: type[BaseProcessBackend] = BaseProcessBackend

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
            default = next(iter(self._matching_process_names()))
        except StopIteration:
            raise CommandError(
                f"No {self.process_label}s configured in the PRODUCTION_PROCESSES "
                f"setting.\nConfigure your {self.process_label}s before running this "
                "command."
            ) from None
        parser.add_argument(
            "process_name",
            type=str,
            choices=choices,
            nargs="?",
            default=default,
        )
        parser.add_argument("--list", action="store_true")

    def _matching_process_names(self) -> list[str]:
        """
        Return the configured process names runnable by this command.

        Each configured backend is imported and classified as a server or
        worker backend; names whose backend subclasses
        :attr:`backend_base_class` are returned. A misconfigured or
        unclassifiable backend raises :class:`CommandError` so the problem
        surfaces instead of being silently hidden.
        """
        try:
            processes = app_settings.PRODUCTION_PROCESSES.items()
        except AttributeError:
            raise CommandError(
                "PRODUCTION_PROCESSES setting has been configured incorrectly.\n"
                "Check the documentation to configure this setting correctly."
            ) from None

        matching = []
        for process_name, process_config in processes:
            try:
                backend_path = process_config["BACKEND"]
            except KeyError:
                raise CommandError(
                    f"Backend not configured for process named '{process_name}'"
                ) from None
            try:
                backend_class = import_string(backend_path)
            except ImportError as e:
                raise CommandError(
                    f"Backend '{backend_path}' configured for process named "
                    f"'{process_name}' could not be imported: {e}"
                ) from None
            if not (
                isinstance(backend_class, type)
                and issubclass(backend_class, (BaseServerBackend, BaseWorkerBackend))
            ):
                raise CommandError(
                    f"Backend '{backend_path}' configured for process named "
                    f"'{process_name}' is not a server or worker backend."
                )
            if issubclass(backend_class, self.backend_base_class):
                matching.append(process_name)
        return matching

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
            self.start_process(*args, **cmd_options)
        except CommandError as e:
            if options.traceback:
                raise

            # SystemCheckError takes care of its own formatting.
            if isinstance(e, SystemCheckError):
                self.stderr.write(str(e), lambda x: x)
            else:
                self.stderr.write(f"{e.__class__.__name__}: {e}")
            sys.exit(e.returncode)

    def start_process(
        self, process_name: str, *args: list[str], **kwargs: Mapping[str, str]
    ) -> None:
        """Start the correct process based on the provided name."""
        try:
            process_config = app_settings.PRODUCTION_PROCESSES[process_name]
        except KeyError:
            available = "\n ".join(app_settings.PRODUCTION_PROCESSES.keys())
            label = self.process_label.capitalize()
            raise CommandError(
                f"{label} named '{process_name}' not found in the "
                f"PRODUCTION_PROCESSES setting\nAvailable names are:\n {available}"
            ) from None

        try:
            backend_path = process_config["BACKEND"]
        except KeyError:
            raise CommandError(
                f"Backend not configured for {self.process_label} named {process_name}"
            ) from None

        backend_class = import_string(backend_path)

        if isinstance(backend_class, type) and not issubclass(
            backend_class, self.backend_base_class
        ):
            raise CommandError(
                self._wrong_backend_message(process_name, backend_path, backend_class)
            )

        self.stdout.write(
            self.style.NOTICE(f"Starting {self.process_label} named {process_name}")
        )

        backend = backend_class(**process_config)
        backend.start_server(*backend.prep_server_args())

    def _wrong_backend_message(
        self, process_name: str, backend_path: str, backend_class: type
    ) -> str:
        hint = ""
        if issubclass(backend_class, BaseWorkerBackend):
            hint = (
                f"\nThat backend is a worker backend; run "
                f"`python manage.py worker {process_name}` instead."
            )
        elif issubclass(backend_class, BaseServerBackend):
            hint = (
                f"\nThat backend is a server backend; run "
                f"`python manage.py server {process_name}` instead."
            )
        return (
            f"Backend '{backend_path}' configured for {self.process_label} named "
            f"'{process_name}' is not a valid {self.process_label} backend.{hint}"
        )

    def list_process_names(self) -> None:
        """Simple function to return a list of the configured processes."""
        available = "\n ".join(self._matching_process_names())
        self.stdout.write(
            self.style.SUCCESS(
                f"Available {self.process_label} process names are:\n {available}"
            )
        )
