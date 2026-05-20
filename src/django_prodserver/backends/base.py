from collections.abc import Collection, Mapping
from typing import Any


def _option_name(token: str) -> str | None:
    """
    Return the option name for a command-line token.

    The name is the text before any ``=`` (e.g. ``--bind`` for
    ``--bind=0.0.0.0:8000``). Tokens that are not options -- they do not start
    with ``-``, such as a bare value in ``--timeout 30`` -- return ``None``.
    """
    if not token.startswith("-"):
        return None
    return token.split("=", 1)[0]


class BaseProcessBackend:
    """
    Base class to configure an individual process backend.

    You are required to override ``start_server`` in the subclass. Most
    backends should subclass :class:`BaseServerBackend` (for web/ASGI/WSGI
    servers) or :class:`BaseWorkerBackend` (for background task workers)
    rather than this class directly so the ``server`` and ``worker``
    management commands can tell the two apart.

    {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8111"}
    }
    """

    #: Whether this backend can accept extra command-line arguments forwarded
    #: from the ``server``/``worker`` command. Backends that construct their
    #: server programmatically (rather than from an argv list) should set this
    #: to ``False`` so unusable arguments fail loudly instead of being dropped.
    accepts_extra_args: bool = True

    def __init__(self, **server_args: Any) -> None:
        self.args = self._format_server_args_from_dict(server_args.get("ARGS", {}))

    def start_server(self, *args: str) -> None:
        """
        Function is called to start the process directly.

        This must be implemented in the subclass
        """
        raise NotImplementedError

    def prep_server_args(self, extra_args: Collection[str] = ()) -> list[str]:
        """
        Here we customisation of the arguments passed to the server process.

        Typically this is where fixed arguments are inserted into the args.
        ``extra_args`` holds any arguments forwarded from the command line.
        They are appended after the arguments configured in settings and take
        precedence over any configured argument that shares the same option
        name.
        """
        return [*self._configured_args(extra_args), *extra_args]

    def overridden_args(self, extra_args: Collection[str] = ()) -> list[str]:
        """
        Return the configured args that ``extra_args`` overrides.

        A configured argument is overridden when ``extra_args`` contains an
        option with the same name, so the command-line value wins.
        """
        cli_options = {
            name for name in map(_option_name, extra_args) if name is not None
        }
        return [arg for arg in self.args if _option_name(arg) in cli_options]

    def _configured_args(self, extra_args: Collection[str]) -> list[str]:
        """Return configured args with anything overridden by ``extra_args`` dropped."""
        overridden = set(self.overridden_args(extra_args))
        return [arg for arg in self.args if arg not in overridden]

    def _format_server_args_from_dict(
        self, args: str | Mapping[str, str | Collection[str] | None]
    ) -> list[str]:
        """
        Formatting server process arguments coming from settings.

        This function transforms the dictionary settings configuration
        from:
            {
                "bind": "0.0.0.0:8111",
                "preload": None,
            }
        to
            [
                "--bind=0.0.0.0:8111",
                "--preload",
            ]
        """
        if isinstance(args, str):
            return [args]

        def format_arg(arg_name: str, arg_value: str | Collection[str] | None) -> str:
            if arg_value is None:
                return f"--{arg_name}"
            return f"--{arg_name}={arg_value}"

        return [format_arg(arg_name, arg_value) for arg_name, arg_value in args.items()]

    # def run_from_argv(self, argv):
    # TODO: The below should be looked into and implemented
    #     if getattr(settings, "WEBSERVER_WARMUP", True):
    #         app = get_internal_wsgi_application()
    #         if getattr(settings, "WEBSERVER_WARMUP_HEALTHCHECK", None):
    #             wsgi_healthcheck(app, settings.WEBSERVER_WARMUP_HEALTHCHECK)
    #     # self.start_server(*self.prep_server_args())


class BaseServerBackend(BaseProcessBackend):
    """
    Base class for web server backends (WSGI / ASGI).

    Backends that subclass this are runnable via ``python manage.py server``.
    """


class BaseWorkerBackend(BaseProcessBackend):
    """
    Base class for background task worker backends.

    Backends that subclass this are runnable via ``python manage.py worker``.
    """
