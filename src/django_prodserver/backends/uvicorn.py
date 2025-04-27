import uvicorn.main

from ..utils import asgi_app_name, wsgi_app_name
from .base import BaseServerBackend


class UvicornServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """

    def prep_server_args(self):
        args = [asgi_app_name()]
        args.extend(self.args)
        return args

    def start_server(self, *args):
        uvicorn.main.main(args)


class UvicornWSGIServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """

    def prep_server_args(self):
        args = [wsgi_app_name(), "--interface=wsgi"]
        args.extend(self.args)
        return args

    def start_server(self, *args):
        uvicorn.main.main(args)
