from collections.abc import Collection

import waitress.runner

from ...utils import wsgi_app_name
from ..base import BaseServerBackend


class WaitressServer(BaseServerBackend):
    """
    WaitressServer Backend.

    Bypass any Django handling of the command and sends all arguments straight
    to waitress.
    """

    def start_server(self, *args: str) -> None:
        """Start the server."""
        waitress.runner.run(argv=args)

    def prep_server_args(self, extra_args: Collection[str] = ()) -> list[str]:
        """
        Prepare the server args.

        ``waitress-serve`` expects the application module as the final
        positional argument, so forwarded ``extra_args`` are inserted before
        it alongside the settings-configured options.
        """
        return ["waitress", *self.args, *extra_args, wsgi_app_name()]
