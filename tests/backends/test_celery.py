from unittest.mock import Mock, patch

import pytest

# Handle optional dependency
celery = pytest.importorskip("celery")

from django_prodserver.backends.workers.celery import (  # NOQA: E402
    CeleryBeat,
    CeleryWorker,
)


class TestCeleryWorker:
    """Tests for CeleryWorker class."""

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_with_app(self, mock_import_string):
        """Test CeleryWorker initialization with APP config."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {
            "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {"loglevel": "info", "concurrency": "4"},
        }

        worker = CeleryWorker(**server_config)

        assert worker.app == mock_app
        assert worker.args == ["--loglevel=info", "--concurrency=4"]
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_without_args(self, mock_import_string):
        """Test CeleryWorker initialization without ARGS."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"APP": "myproject.celery.app"}

        worker = CeleryWorker(**server_config)

        assert worker.app == mock_app
        assert worker.args == []
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_missing_app(self, mock_import_string):
        """Test CeleryWorker initialization without APP config."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"ARGS": {"loglevel": "info"}}

        CeleryWorker(**server_config)

        # When APP is None/missing, import_string will be called with None
        mock_import_string.assert_called_once_with(None)

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server(self, mock_import_string):
        """Test start_server method."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"APP": "myproject.celery.app"}
        worker = CeleryWorker(**server_config)

        args = ["--loglevel=info", "--concurrency=4"]
        worker.start_server(*args)

        mock_app.start.assert_called_once_with(argv=["worker", *args])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_no_args(self, mock_import_string):
        """Test start_server method with no args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"APP": "myproject.celery.app"}
        worker = CeleryWorker(**server_config)

        worker.start_server()

        mock_app.start.assert_called_once_with(argv=["worker"])

    def test_inheritance_from_base_backend(self):
        """Test that CeleryWorker properly inherits from BaseWorkerBackend."""
        from django_prodserver.backends.base import BaseWorkerBackend

        with patch("django_prodserver.backends.workers.celery.import_string"):
            worker = CeleryWorker(APP="test.app")
            assert isinstance(worker, BaseWorkerBackend)

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_with_empty_args(self, mock_import_string):
        """Test CeleryWorker initialization with empty ARGS dict."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"APP": "myproject.celery.app", "ARGS": {}}

        worker = CeleryWorker(**server_config)

        assert worker.app == mock_app
        assert worker.args == []
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_with_complex_args(self, mock_import_string):
        """Test CeleryWorker initialization with complex ARGS."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {
            "APP": "myproject.celery.app",
            "ARGS": {
                "loglevel": "debug",
                "concurrency": "8",
                "queues": "high,normal,low",
                "prefetch-multiplier": "1",
            },
        }

        worker = CeleryWorker(**server_config)

        expected_args = [
            "--loglevel=debug",
            "--concurrency=8",
            "--queues=high,normal,low",
            "--prefetch-multiplier=1",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in worker.args

        assert len(worker.args) == 4
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_prep_server_args(self, mock_import_string):
        """Test prep_server_args method."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        worker = CeleryWorker(
            APP="myproject.celery.app", ARGS={"loglevel": "info", "concurrency": "2"}
        )
        args = worker.prep_server_args()

        assert args == ["--loglevel=info", "--concurrency=2"]

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_prep_server_args_empty(self, mock_import_string):
        """Test prep_server_args with no args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        worker = CeleryWorker(APP="myproject.celery.app")
        args = worker.prep_server_args()

        assert args == []

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_with_mixed_args(self, mock_import_string):
        """Test start_server with a mix of initialization and runtime args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        # Initialize with some args
        worker = CeleryWorker(
            APP="myproject.celery.app", ARGS={"loglevel": "info", "concurrency": "2"}
        )

        # Start with additional args
        runtime_args = ["--queues=urgent", "--prefetch-multiplier=1"]
        worker.start_server(*runtime_args)

        # Should dispatch through the celery CLI with the worker subcommand
        mock_app.start.assert_called_once_with(argv=["worker", *runtime_args])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_import_string_exception_propagation(self, mock_import_string):
        """Test that import_string exceptions are properly propagated."""
        mock_import_string.side_effect = ImportError("Cannot import celery app")

        with pytest.raises(ImportError, match="Cannot import celery app"):
            CeleryWorker(APP="nonexistent.celery.app")

        mock_import_string.assert_called_once_with("nonexistent.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_worker_start_exception_propagation(self, mock_import_string):
        """Test that worker start exceptions are properly propagated."""
        mock_app = Mock()
        mock_app.start.side_effect = RuntimeError("Worker failed to start")
        mock_import_string.return_value = mock_app

        worker = CeleryWorker(APP="myproject.celery.app")

        with pytest.raises(RuntimeError, match="Worker failed to start"):
            worker.start_server()

        mock_app.start.assert_called_once_with(argv=["worker"])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_worker_creation_exception_propagation(self, mock_import_string):
        """Test that worker creation exceptions are properly propagated."""
        mock_app = Mock()
        mock_app.start.side_effect = ValueError("Invalid worker configuration")
        mock_import_string.return_value = mock_app

        worker = CeleryWorker(APP="myproject.celery.app")

        with pytest.raises(ValueError, match="Invalid worker configuration"):
            worker.start_server("--invalid-arg")

        mock_app.start.assert_called_once_with(argv=["worker", "--invalid-arg"])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_app_attribute_access(self, mock_import_string):
        """Test that the app attribute is properly accessible."""
        mock_app = Mock()
        mock_app.name = "test_celery_app"
        mock_import_string.return_value = mock_app

        worker = CeleryWorker(APP="myproject.celery.app")

        assert worker.app == mock_app
        assert worker.app.name == "test_celery_app"

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_server_config_with_extra_keys(self, mock_import_string):
        """Test that extra configuration keys are ignored properly."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {
            "APP": "myproject.celery.app",
            "ARGS": {"loglevel": "info"},
            "EXTRA_CONFIG": "ignored",
            "ANOTHER_KEY": "123",
        }

        worker = CeleryWorker(**server_config)

        # Should only process APP and ARGS
        assert worker.app == mock_app
        assert worker.args == ["--loglevel=info"]
        mock_import_string.assert_called_once_with("myproject.celery.app")


class TestCeleryBeat:
    """Test CeleryBeat backend."""

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_with_app(self, mock_import_string):
        """Test CeleryBeat initialization with APP config."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {
            "BACKEND": "django_prodserver.backends.workers.celery.CeleryBeat",
            "APP": "myproject.celery.app",
            "ARGS": {"loglevel": "info"},
        }

        worker = CeleryBeat(**server_config)

        assert worker.app == mock_app
        assert worker.args == ["--loglevel=info"]
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_no_args(self, mock_import_string):
        """Test start_server method with no args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {"APP": "myproject.celery.app"}
        beat = CeleryBeat(**server_config)

        beat.start_server()

        mock_app.start.assert_called_once_with(argv=["beat"])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_with_mixed_args(self, mock_import_string):
        """Test start_server with a mix of initialization and runtime args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        # Initialize with some args
        beat = CeleryBeat(APP="myproject.celery.app", ARGS={"loglevel": "info"})

        # Start with additional args
        runtime_args = ["--scheduler=some.Scheduler"]
        beat.start_server(*runtime_args)

        # Should dispatch through the celery CLI with the beat subcommand
        mock_app.start.assert_called_once_with(argv=["beat", *runtime_args])
