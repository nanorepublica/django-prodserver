import waitress.runner

from ..utils import wsgi_app_name
from .base import BaseServerBackend


class WaitressServer(BaseServerBackend):
    """
    This bypasses any Django handling of the command and sends all arguments straight
    to waitress.
    """

    def start_server(self, *args):
        waitress.runner.run(argv=args)

    def prep_server_args(self):
        args = ["waitress"]
        args.extend(self.args)
        args.append(wsgi_app_name())
        return args
