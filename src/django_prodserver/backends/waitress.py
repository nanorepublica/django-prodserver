import waitress.runner

from .base import BaseServerBackend
from ..utils import wsgi_app_name

class WaitressServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to waitress.
    """

    def start_server(self, *args):
        waitress.runner.run(argv=args)

    def prep_server_args(self):
        return ('waitress', ) + self.args + (wsgi_app_name(),)
