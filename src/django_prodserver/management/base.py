import sys
from argparse import ArgumentParser
from collections.abc import Collection, Mapping

from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError
from django.utils.module_loading import import_string

from ..backends.base import (
    BaseProcessBackend,
    BaseServerBackend,
    BaseWorkerBackend,
)
from ..conf import app_settings


def _option_name(token: str) -> str | None:
    """Return a token's option name (text before ``=``), or None if not an option."""
    if not token.startswith("-"):
        return None
    return token.split("=", 1)[0]


def split_extra_args(
    extra_args: Collection[str], configured: Mapping[str, object]
) -> tuple[dict[str, str | None], list[str]]:
    """
    Split forwarded command-line args into ARGS overrides and new arguments.

    An *override* is a ``--name`` / ``--name=value`` token whose ``name``
    matches a key configured in ``ARGS``; its value replaces the configured
    one. For a configured option that expects a value, a following
    space-separated token is consumed as that value. Every other token is
    returned untouched as a *new* argument.
    """
    overrides: dict[str, str | None] = {}
    new_args: list[str] = []
    tokens = iter(extra_args)
    for token in tokens:
        name = _option_name(token)
        key = name[2:] if name is not None and name.startswith("--") else None
        if key is None or key not in configured:
            new_args.append(token)
            continue
        if "=" in token:
            overrides[key] = token.split("=", 1)[1]
        elif configured[key] is None:
            overrides[key] = None
        else:
            overrides[key] = next(tokens, None)
    return overrides, new_args


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
            default = next(iter(choices))
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

    def run_from_argv(self, argv: list[str]) -> None:
        """
        Slight modification of the BaseCommand function.

        Set up any environment changes requested (e.g., Python path and
        Django settings), run Django's system checks unless ``--skip-checks``
        is given, then run this command. Arguments not recognised by this
        command are forwarded to the underlying process backend. If the
        command raises a ``CommandError``, intercept it and print it sensibly
        to stderr. If the ``--traceback`` option is present or the raised
        ``Exception`` is not ``CommandError``, raise it.
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])

        options, extra_args = parser.parse_known_args(argv[2:])
        cmd_options = vars(options)
        # Move positional args out of options to mimic legacy optparse
        args = cmd_options.pop("args", ())
        handle_default_options(options)

        if cmd_options["list"]:
            self.list_process_names()
            return

        try:
            if not options.skip_checks:
                self.stdout.write("Performing system checks...\n")
                self.check(display_num_errors=True)
            self.start_process(*args, extra_args=extra_args, **cmd_options)
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
        self,
        process_name: str,
        *args: str,
        extra_args: Collection[str] = (),
        **kwargs: object,
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

        configured_args = process_config.get("ARGS", {})
        if not isinstance(configured_args, Mapping):
            configured_args = {}
        overrides, new_args = split_extra_args(extra_args, configured_args)

        if new_args and not backend_class.accepts_extra_args:
            raise CommandError(
                f"The '{backend_path}' backend configured for "
                f"{self.process_label} named '{process_name}' only accepts "
                "command-line arguments that override an entry in its ARGS "
                f"setting; these do not: {' '.join(new_args)}"
            )

        if overrides:
            process_config = {
                **process_config,
                "ARGS": {**configured_args, **overrides},
            }
            for key in overrides:
                self.stdout.write(
                    self.style.WARNING(
                        f"Overriding configured argument '--{key}' with "
                        "command-line value"
                    )
                )

        backend = backend_class(**process_config)

        self.stdout.write(
            self.style.NOTICE(f"Starting {self.process_label} named {process_name}")
        )
        backend.start_server(*backend.prep_server_args(new_args))

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
        available = "\n ".join(app_settings.PRODUCTION_PROCESSES.keys())
        self.stdout.write(
            self.style.SUCCESS(
                f"Available {self.process_label} process names are:\n {available}"
            )
        )
