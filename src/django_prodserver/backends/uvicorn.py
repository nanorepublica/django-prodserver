import uvicorn.main

from ..utils import asgi_app_name, wsgi_app_name
from .base import BaseServerBackend


class UvicornServer(BaseServerBackend):
    """
    Uvicorn ASGIServer Backend.

    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """

    def prep_server_args(self) -> list[str]:
        """Prepare the server args."""
        args = [asgi_app_name()]
        args.extend(self.args)
        return args

    def start_server(self, *args: str) -> None:
        """Start the server."""
        uvicorn.main.main(args)


class UvicornWSGIServer(BaseServerBackend):
    """
    Uvicorn WSGIServer Backend.

    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """

    def prep_server_args(self) -> list[str]:
        """Prepare the server args."""
        args = [wsgi_app_name(), "--interface=wsgi"]
        args.extend(self.args)
        return args

    def start_server(self, *args: str) -> None:
        """Start the server."""
        uvicorn.main.main(args)
