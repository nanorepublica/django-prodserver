from ...backends.base import BaseServerBackend
from ..base import BaseProcessCommand


class Command(BaseProcessCommand):
    """The main server command."""

    help = "Start a configured production server process."
    process_label = "server"
    backend_base_class = BaseServerBackend
