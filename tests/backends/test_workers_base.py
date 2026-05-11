import importlib
import warnings

import pytest

from django_prodserver.backends.base import (
    BaseProcessBackend,
    BaseServerBackend,
    BaseWorkerBackend,
)


def test_worker_backend_is_a_process_backend():
    assert issubclass(BaseWorkerBackend, BaseProcessBackend)
    assert not issubclass(BaseWorkerBackend, BaseServerBackend)
    assert not issubclass(BaseServerBackend, BaseWorkerBackend)


def test_worker_backend_start_server_not_implemented():
    backend = BaseWorkerBackend()
    with pytest.raises(NotImplementedError):
        backend.start_server()


def test_worker_backend_formats_args_like_process_backend():
    backend = BaseWorkerBackend(ARGS={"queues": "high", "burst": None})
    assert backend.prep_server_args() == ["--queues=high", "--burst"]


@pytest.mark.parametrize(
    ("module_name", "attr_names"),
    [
        ("django_prodserver.backends.celery", ["CeleryWorker", "CeleryBeat"]),
        ("django_prodserver.backends.django_tasks", ["DjangoTasksWorker"]),
        ("django_prodserver.backends.django_q2", ["DjangoQ2Worker"]),
    ],
)
def test_legacy_backend_modules_warn_and_reexport(module_name, attr_names):
    legacy = importlib.import_module(module_name)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(legacy)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)

    new = importlib.import_module(module_name.replace("backends.", "backends.workers."))
    for attr in attr_names:
        assert getattr(legacy, attr) is getattr(new, attr)
        assert issubclass(getattr(new, attr), BaseWorkerBackend)
