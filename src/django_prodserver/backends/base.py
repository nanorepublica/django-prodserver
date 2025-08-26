from collections.abc import Collection, Mapping
from typing import Any


class BaseServerBackend:
    """
    Base class to configure an individual process backend.

    You are required to override "start_server" in the subclass

    {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8111"}
    }
    """

    def __init__(self, **server_args: Any) -> None:
        self.args = self._format_server_args_from_dict(server_args.get("ARGS", {}))

    def start_server(self, *args: str) -> None:
        """
        Function is called to start the process directly.

        This must be implemented in the subclass
        """
        raise NotImplementedError

    def prep_server_args(self) -> list[str]:
        """
        Here we customisation of the arguments passed to the server process.

        Typically this is where fixed arguments are inserted into the args
        """
        return self.args

    def _format_server_args_from_dict(
        self, args: str | Mapping[str, str | Collection[str]]
    ) -> list[str]:
        """
        Formatting server process arguments coming from settings.

        This function transforms the dictionary settings configuration
        from:
            {
                "bind": "0.0.0.0:8111"
            }
        to
            [
                "--bind=0.0.0.0:8111"
            ]
        """
        if isinstance(args, str):
            return [args]
        return [f"--{arg_name}={arg_value}" for arg_name, arg_value in args.items()]

    # def run_from_argv(self, argv):
    # TODO: The below should be looked into and implemented
    #     if getattr(settings, "WEBSERVER_WARMUP", True):
    #         app = get_internal_wsgi_application()
    #         if getattr(settings, "WEBSERVER_WARMUP_HEALTHCHECK", None):
    #             wsgi_healthcheck(app, settings.WEBSERVER_WARMUP_HEALTHCHECK)
    #     # self.start_server(*self.prep_server_args())
