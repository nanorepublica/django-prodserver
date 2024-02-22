import uvicorn.main

from .base import BaseServerBackend
from ..utils import wsgi_app_name, asgi_app_name

class UvicornServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """
    def prep_server_args(self):
        return (asgi_app_name(),) + self.args

    def start_server(self, *args):
        uvicorn.main.main(args)



class UvicornWSGIServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to uvicorn.
    """
    def prep_server_args(self):
        return (wsgi_app_name(),"--interface=wsgi") + self.args

    def start_server(self, *args):
        uvicorn.main.main(args)
