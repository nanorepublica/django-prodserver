from ...backends.base import BaseWorkerBackend
from ..base import BaseProcessCommand


class Command(BaseProcessCommand):
    """Start a configured background task worker process."""

    help = "Start a configured background task worker process."
    process_label = "worker"
    backend_base_class = BaseWorkerBackend
