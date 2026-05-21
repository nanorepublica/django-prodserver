from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.management import CommandError
from django.test import TestCase, override_settings

from django_prodserver.backends.base import BaseServerBackend
from django_prodserver.management.base import BaseProcessCommand
from django_prodserver.management.commands.worker import Command

DJANGO_TASKS_WORKER = (
    "django_prodserver.backends.workers.django_tasks.DjangoTasksWorker"
)


class _DummyServerBackend(BaseServerBackend):
    """A server backend used to exercise the worker command's validation."""

    def start_server(self, *args: str) -> None:  # pragma: no cover - never run
        raise AssertionError("should not be started by the worker command")


DUMMY_SERVER = "tests.test_worker_command._DummyServerBackend"
ONE_WORKER = {"worker": {"BACKEND": DJANGO_TASKS_WORKER}}


class TestWorkerCommand(TestCase):
    """Tests for the worker management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = Command()
        self.command.stdout = StringIO()
        self.command.stderr = StringIO()

    def test_command_subclasses_base_process_command(self):
        """The worker command shares the implementation with `server`."""
        assert issubclass(Command, BaseProcessCommand)
        assert self.command.process_label == "worker"

    def test_command_instance_creation(self):
        """Test that command can be instantiated."""
        assert isinstance(Command(), Command)

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": DUMMY_SERVER},
            "worker": {"BACKEND": DJANGO_TASKS_WORKER},
        }
    )
    def test_add_arguments_with_choices(self):
        """Test that add_arguments sets up choices correctly."""
        parser = MagicMock()
        self.command.add_arguments(parser)

        calls = parser.add_argument.call_args_list
        args, kwargs = calls[0]
        assert args[0] == "process_name"
        assert set(kwargs["choices"]) == {"web", "worker"}

        args, kwargs = calls[1]
        assert args[0] == "--list"
        assert kwargs["action"] == "store_true"

    @override_settings(PRODUCTION_PROCESSES={})
    def test_add_arguments_no_workers_configured(self):
        """add_arguments raises CommandError when nothing is configured."""
        with pytest.raises(CommandError) as exc_info:
            self.command.add_arguments(MagicMock())

        assert "No workers configured in the PRODUCTION_PROCESSES setting" in str(
            exc_info.value
        )

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": DUMMY_SERVER},
            "worker": {"BACKEND": DJANGO_TASKS_WORKER},
        }
    )
    def test_list_process_names(self):
        """Test list_process_names method."""
        self.command.list_process_names()

        output = self.command.stdout.getvalue()
        assert "web" in output
        assert "worker" in output
        assert "Available worker process names are:" in output

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django.core.management.call_command")
    def test_start_process_runs_worker_backend(self, mock_call_command):
        """Starting a worker backend invokes the underlying process."""
        self.command.start_process("worker")

        mock_call_command.assert_called_once_with("db_worker")
        assert "Starting worker named worker" in self.command.stdout.getvalue()

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django.core.management.call_command")
    @patch("sys.exit")
    def test_run_from_argv_start_worker(self, mock_exit, mock_call_command):
        """Test run_from_argv starting a worker."""
        self.command.run_from_argv(["manage.py", "worker", "worker"])

        mock_call_command.assert_called_once_with("db_worker")
        mock_exit.assert_not_called()

    @override_settings(PRODUCTION_PROCESSES={"web": {"BACKEND": DUMMY_SERVER}})
    def test_worker_command_rejects_server_backend(self):
        """The worker command refuses to start a server backend."""
        with pytest.raises(CommandError) as exc_info:
            self.command.start_process("web")

        message = str(exc_info.value)
        assert "is not a valid worker backend" in message
        assert "python manage.py server web" in message

    def test_start_process_nonexistent_worker(self):
        """Test start_process with a name that is not configured."""
        with pytest.raises(CommandError) as exc_info:
            self.command.start_process("nonexistent")

        assert "Worker named 'nonexistent' not found" in str(exc_info.value)

    @override_settings(PRODUCTION_PROCESSES={"worker": {}})  # Missing BACKEND
    def test_start_process_missing_backend(self):
        """Test start_process with missing BACKEND configuration."""
        with pytest.raises(CommandError) as exc_info:
            self.command.start_process("worker")

        assert "Backend not configured for worker named worker" in str(exc_info.value)

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django_prodserver.management.base.import_string")
    @patch("sys.exit")
    def test_run_from_argv_command_error(self, mock_exit, mock_import_string):
        """Test run_from_argv converts CommandError to an exit code."""
        mock_import_string.side_effect = CommandError("boom")

        self.command.run_from_argv(["manage.py", "worker", "worker"])

        mock_exit.assert_called_with(1)

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django_prodserver.management.base.import_string")
    def test_run_from_argv_list_option(self, mock_import_string):
        """Test run_from_argv with --list option short-circuits."""
        with patch.object(self.command, "list_process_names") as mock_list:
            self.command.run_from_argv(["manage.py", "worker", "--list"])
            mock_list.assert_called_once()
        mock_import_string.assert_not_called()

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django_prodserver.management.base.import_string")
    def test_start_process_passes_full_config(self, mock_import_string):
        """The whole process config is passed to the backend constructor."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        with override_settings(
            PRODUCTION_PROCESSES={
                "worker": {"BACKEND": DJANGO_TASKS_WORKER, "ARGS": {"queues": "high"}}
            }
        ):
            self.command.start_process("worker")

        mock_backend_class.assert_called_once_with(
            BACKEND=DJANGO_TASKS_WORKER, ARGS={"queues": "high"}
        )
        mock_backend_instance.start_server.assert_called_once()

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django_prodserver.management.base.import_string")
    @patch("sys.exit")
    def test_run_from_argv_runs_system_checks(self, mock_exit, mock_import_string):
        """The worker command runs Django system checks before starting."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.accepts_extra_args = True
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        with patch.object(self.command, "check") as mock_check:
            self.command.run_from_argv(["manage.py", "worker", "worker"])

        mock_check.assert_called_once()
        mock_backend_instance.start_server.assert_called_once()

    @override_settings(PRODUCTION_PROCESSES=ONE_WORKER)
    @patch("django_prodserver.management.base.import_string")
    @patch("sys.exit")
    def test_run_from_argv_forwards_extra_args(self, mock_exit, mock_import_string):
        """Unrecognized CLI args are forwarded to the worker backend."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        with patch.object(self.command, "check"):
            self.command.run_from_argv(
                ["manage.py", "worker", "worker", "--queues=high"]
            )

        mock_backend_instance.prep_server_args.assert_called_once_with(
            ["--queues=high"]
        )
        mock_exit.assert_not_called()
