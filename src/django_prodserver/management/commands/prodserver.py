import sys
from django.conf import settings
from django.core.management import BaseCommand, CommandError, handle_default_options
from django.core.management.base import SystemCheckError
from django.utils.module_loading import import_string


class Command(BaseCommand):
    def add_arguments(self, parser):
        choices = settings.PRODUCTION_PROCESSES.keys()
        parser.add_argument(
            "server_name",
            type=str,
            choices=choices,
            nargs="?",
            default=list(choices)[0],
        )
        parser.add_argument("--list", action="store_true")

    def run_from_argv(self, argv):
        """
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
                self.stderr.write("%s: %s" % (e.__class__.__name__, e))
            sys.exit(e.returncode)

    def start_server(self, server_name, *args, **kwargs):
        # this try/except could be removed, keeping for now as it's a nicer
        try:
            server_config = settings.PRODUCTION_PROCESSES[server_name]
        except KeyError:
            available_servers = "\n ".join(settings.PRODUCTION_PROCESSES.keys())
            raise CommandError(
                "Server named '{}' not found in the PRODUCTION_PROCESSES setting\nAvailable names are:\n {}".format(
                    server_name, available_servers
                )
            )

        self.stdout.write(self.style.NOTICE("Starting server named %s" % server_name))

        try:
            server_backend = server_config["BACKEND"]
        except KeyError:
            raise CommandError("Backend not configured for server named {}".format(server_name))

        backend_class = import_string(server_backend)

        backend = backend_class(**server_config)
        backend.start_server(*backend.prep_server_args())

    def list_process_names(self):
        available_servers = "\n ".join(settings.PRODUCTION_PROCESSES.keys())
        self.stdout.write(self.style.SUCCESS("Available production process names are:\n %s" % available_servers))
