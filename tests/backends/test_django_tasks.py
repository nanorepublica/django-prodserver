import pytest
from unittest.mock import Mock, patch

from django_prodserver.backends.django_tasks import DjangoTasksWorker


class TestDjangoTasksWorker:
    """Tests for DjangoTasksWorker class."""

    def test_init_without_args(self):
        """Test DjangoTasksWorker initialization without args."""
        worker = DjangoTasksWorker()
        assert worker.args == []

    def test_init_with_args(self):
        """Test DjangoTasksWorker initialization with args."""
        worker = DjangoTasksWorker(ARGS={"queues": "default", "threads": "4"})
        assert worker.args == ["--queues=default", "--threads=4"]

    @patch("django.core.management.call_command")
    def test_start_server(self, mock_call_command):
        """Test start_server method."""
        worker = DjangoTasksWorker()
        args = ["--queues=default", "--threads=4"]

        worker.start_server(*args)

        mock_call_command.assert_called_once_with("db_worker", *args)

    @patch("django.core.management.call_command")
    def test_start_server_no_args(self, mock_call_command):
        """Test start_server method with no args."""
        worker = DjangoTasksWorker()

        worker.start_server()

        mock_call_command.assert_called_once_with("db_worker")

    def test_prep_server_args(self):
        """Test prep_server_args method."""
        worker = DjangoTasksWorker(ARGS={"queues": "default"})
        args = worker.prep_server_args()
        assert args == ["--queues=default"]

    def test_prep_server_args_empty(self):
        """Test prep_server_args with no args."""
        worker = DjangoTasksWorker()
        args = worker.prep_server_args()
        assert args == []

    def test_inheritance_from_base_backend(self):
        """Test that DjangoTasksWorker properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        worker = DjangoTasksWorker()
        assert isinstance(worker, BaseServerBackend)

    def test_init_with_empty_args(self):
        """Test DjangoTasksWorker initialization with empty ARGS dict."""
        worker = DjangoTasksWorker(ARGS={})
        assert worker.args == []

    def test_init_with_complex_args(self):
        """Test DjangoTasksWorker initialization with complex ARGS."""
        worker = DjangoTasksWorker(
            ARGS={
                "queues": "high,normal,low",
                "threads": "8",
                "sleep": "5",
                "batch-size": "10",
            }
        )

        expected_args = [
            "--queues=high,normal,low",
            "--threads=8",
            "--sleep=5",
            "--batch-size=10",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in worker.args

        assert len(worker.args) == 4

    @patch("django.core.management.call_command")
    def test_start_server_with_various_args(self, mock_call_command):
        """Test start_server with various argument types."""
        worker = DjangoTasksWorker()
        args = ["--queues=urgent", "--threads=2", "--sleep=1"]

        worker.start_server(*args)

        mock_call_command.assert_called_once_with("db_worker", *args)

    @patch("django.core.management.call_command")
    def test_start_server_single_arg(self, mock_call_command):
        """Test start_server with a single argument."""
        worker = DjangoTasksWorker()

        worker.start_server("--verbose")

        mock_call_command.assert_called_once_with("db_worker", "--verbose")

    @patch("django.core.management.call_command")
    def test_full_workflow(self, mock_call_command):
        """Test the complete workflow from initialization to server start."""
        worker = DjangoTasksWorker(ARGS={"queues": "default", "threads": "4"})
        prepared_args = worker.prep_server_args()
        worker.start_server(*prepared_args)

        mock_call_command.assert_called_once_with(
            "db_worker", "--queues=default", "--threads=4"
        )

    @patch("django.core.management.call_command")
    def test_management_command_exception_propagation(self, mock_call_command):
        """Test that management command exceptions are properly propagated."""
        mock_call_command.side_effect = RuntimeError("db_worker command failed")

        worker = DjangoTasksWorker()

        with pytest.raises(RuntimeError, match="db_worker command failed"):
            worker.start_server("--queues=default")

        mock_call_command.assert_called_once_with("db_worker", "--queues=default")

    @patch("django.core.management.call_command")
    def test_management_command_import_error_propagation(self, mock_call_command):
        """Test that import errors from management are properly propagated."""
        from django.core.management import CommandError

        mock_call_command.side_effect = CommandError("Unknown command: db_worker")

        worker = DjangoTasksWorker()

        with pytest.raises(CommandError, match="Unknown command: db_worker"):
            worker.start_server()

        mock_call_command.assert_called_once_with("db_worker")

    def test_server_args_formatting_special_characters(self):
        """Test that server args with special characters are properly formatted."""
        worker = DjangoTasksWorker(
            ARGS={
                "queues": "queue-with-dashes",
                "log-level": "DEBUG",
                "database-url": "sqlite:///test.db",
            }
        )

        expected_args = [
            "--queues=queue-with-dashes",
            "--log-level=DEBUG",
            "--database-url=sqlite:///test.db",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in worker.args

        assert len(worker.args) == 3

    def test_init_with_extra_config_keys(self):
        """Test that extra configuration keys are ignored properly."""
        worker = DjangoTasksWorker(
            ARGS={"queues": "default"},
            EXTRA_CONFIG="ignored",
            ANOTHER_KEY=123,
        )

        # Should only process ARGS
        assert worker.args == ["--queues=default"]

    @patch("django.core.management.call_command")
    def test_start_server_empty_string_args(self, mock_call_command):
        """Test start_server with empty string arguments."""
        worker = DjangoTasksWorker()

        worker.start_server("", "--queues=default", "")

        mock_call_command.assert_called_once_with(
            "db_worker", "", "--queues=default", ""
        )

    def test_db_worker_command_name_constant(self):
        """Test that the db_worker command name is consistent."""
        worker = DjangoTasksWorker()

        with patch("django.core.management.call_command") as mock_call_command:
            worker.start_server("--test")

            # Verify the command name is always "db_worker"
            args, kwargs = mock_call_command.call_args
            assert args[0] == "db_worker"

    @patch("django.core.management.call_command")
    def test_start_server_with_kwargs_ignored(self, mock_call_command):
        """Test that start_server only accepts positional args."""
        worker = DjangoTasksWorker()

        # start_server signature only accepts *args, no **kwargs
        worker.start_server("--queues=default", "--threads=2")

        mock_call_command.assert_called_once_with(
            "db_worker", "--queues=default", "--threads=2"
        )

    def test_args_property_immutable_after_init(self):
        """Test that args property reflects initialization state."""
        worker = DjangoTasksWorker(ARGS={"queues": "test"})
        original_args = worker.args.copy()

        # Args should be the same after calling other methods
        worker.prep_server_args()

        assert worker.args == original_args
