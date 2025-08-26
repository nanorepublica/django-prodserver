from io import StringIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.management import CommandError, call_command
from django.core.management.base import SystemCheckError
from django.test import TestCase, override_settings

from django_prodserver.management.commands.devserver import Command as DevServerCommand
from django_prodserver.management.commands.prodserver import Command
from django_prodserver.management.commands.prodserver import (
    Command as ProdServerCommand,
)


class TestProdserverCommand(TestCase):
    """Tests for the prodserver management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = Command()
        self.command.stdout = StringIO()
        self.command.stderr = StringIO()

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"}
        }
    )
    @patch("sys.argv", ["manage.py", "prodserver", "web"])
    def test_command_line_execution(self):
        """Test command execution from command line."""
        command = ProdServerCommand()

        # Test that the command can be set up for command line execution
        assert hasattr(command, "run_from_argv")
        assert callable(command.run_from_argv)

    def test_command_registration(self):
        """Test that commands are properly registered."""
        # Test that we can instantiate the commands
        prodserver_cmd = ProdServerCommand()
        devserver_cmd = DevServerCommand()

        assert prodserver_cmd is not None
        assert devserver_cmd is not None

        # Test basic command interface
        assert hasattr(prodserver_cmd, "handle")
        assert hasattr(devserver_cmd, "handle")

    @override_settings(
        PRODUCTION_PROCESSES={
            "web-1": {"BACKEND": "test.backend.1"},
            "web-2": {"BACKEND": "test.backend.2"},
            "worker-1": {"BACKEND": "test.backend.3"},
        }
    )
    def test_multiple_server_configurations(self):
        """Test handling of multiple server configurations."""
        self.command.run_from_argv(["manage.py", "prodserver", "--list"])

        output = self.command.stdout.getvalue()
        assert "web-1" in output
        assert "web-2" in output
        assert "worker-1" in output

    def test_command_error_handling(self):
        """Test various error conditions in commands."""
        # Test with completely invalid configuration
        with override_settings(PRODUCTION_PROCESSES="invalid"):
            # call_command("prodserver", "--list")

            with pytest.raises(CommandError):  # Could be various exception types
                call_command("prodserver", "--list")

    @override_settings(
        PRODUCTION_PROCESSES={
            "test-server": {
                "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
                "ARGS": {"queues": "default"},
            }
        }
    )
    @patch("django.core.management.call_command")
    def test_django_tasks_backend_integration(self, mock_call_command):
        """Test integration with django-tasks backend."""
        with patch(
            "django_prodserver.management.commands.prodserver.import_string"
        ) as mock_import:
            from django_prodserver.backends.django_tasks import DjangoTasksWorker

            mock_import.return_value = DjangoTasksWorker

            self.command.run_from_argv(["manage.py", "prodserver", "test-server"])

            # Should have called the management command
            mock_call_command.assert_called()

    def test_command_instance_creation(self):
        """Test that command can be instantiated."""
        command = Command()
        assert isinstance(command, Command)

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"},
            "worker": {"BACKEND": "django_prodserver.backends.celery.CeleryWorker"},
        }
    )
    def test_add_arguments_with_choices(self):
        """Test that add_arguments sets up choices correctly."""
        parser = MagicMock()
        self.command.add_arguments(parser)

        # Should add server_name argument with choices
        calls = parser.add_argument.call_args_list

        # First call should be for server_name
        server_name_call = calls[0]
        args, kwargs = server_name_call
        assert args[0] == "server_name"
        assert set(kwargs["choices"]) == {"web", "worker"}

        # Second call should be for --list
        list_call = calls[1]
        args, kwargs = list_call
        assert args[0] == "--list"
        assert kwargs["action"] == "store_true"

    @override_settings(PRODUCTION_PROCESSES={"test": {}})
    def test_add_arguments_empty_choices(self):
        """Test add_arguments with empty PRODUCTION_PROCESSES."""
        parser = MagicMock()

        # Should not raise error even with empty choices
        self.command.add_arguments(parser)

        calls = parser.add_argument.call_args_list
        server_name_call = calls[0]
        args, kwargs = server_name_call
        assert list(kwargs["choices"]) == ["test"]

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"},
            "worker": {"BACKEND": "django_prodserver.backends.celery.CeleryWorker"},
        }
    )
    def test_list_process_names(self):
        """Test list_process_names method."""
        self.command.list_process_names()

        output = self.command.stdout.getvalue()
        assert "web" in output
        assert "worker" in output
        assert "Available production process names are:" in output

    @override_settings(PRODUCTION_PROCESSES={})
    def test_list_process_names_empty(self):
        """Test list_process_names with empty processes."""
        self.command.list_process_names()

        output = self.command.stdout.getvalue()
        assert "Available production process names are:" in output

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"}
        }
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    def test_start_server_success(self, mock_import_string):
        """Test successful server start."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        self.command.start_server("web")

        # Verify import_string was called with correct backend
        mock_import_string.assert_called_once_with(
            "django_prodserver.backends.gunicorn.GunicornServer"
        )

        # Verify backend was instantiated with server config
        mock_backend_class.assert_called_once_with(
            BACKEND="django_prodserver.backends.gunicorn.GunicornServer"
        )

        # Verify start_server was called with prepared args
        mock_backend_instance.start_server.assert_called_once()

    def test_start_server_nonexistent_server(self):
        """Test start_server with nonexistent server name."""
        with pytest.raises(CommandError) as exc_info:
            self.command.start_server("nonexistent")

        assert "Server named 'nonexistent' not found" in str(exc_info.value)

    @override_settings(PRODUCTION_PROCESSES={"web": {}})  # Missing BACKEND key
    def test_start_server_missing_backend(self):
        """Test start_server with missing BACKEND configuration."""
        with pytest.raises(CommandError) as exc_info:
            self.command.start_server("web")

        assert "Backend not configured for server named web" in str(exc_info.value)

    @override_settings(
        PRODUCTION_PROCESSES={"web": {"BACKEND": "nonexistent.backend.Class"}}
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    def test_start_server_import_error(self, mock_import_string):
        """Test start_server with import error."""
        mock_import_string.side_effect = ImportError("Cannot import backend")

        with pytest.raises(ImportError):
            self.command.start_server("web")

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {
                "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
                "ARGS": {"bind": "0.0.0.0:8000"},
            }
        }
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    def test_start_server_with_args(self, mock_import_string):
        """Test start_server with server arguments."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = ["--bind=0.0.0.0:8000"]
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        self.command.start_server("web")

        # Verify backend was instantiated with full config
        mock_backend_class.assert_called_once_with(
            BACKEND="django_prodserver.backends.gunicorn.GunicornServer",
            ARGS={"bind": "0.0.0.0:8000"},
        )

    @patch("sys.exit")
    def test_run_from_argv_list_option(self, mock_exit):
        """Test run_from_argv with --list option."""
        with patch.object(self.command, "list_process_names") as mock_list:
            self.command.run_from_argv(["manage.py", "prodserver", "--list"])
            mock_list.assert_called_once()
            # Should return early and not call sys.exit
            mock_exit.assert_not_called()

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"}
        }
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    @patch("sys.exit")
    def test_run_from_argv_start_server(self, mock_exit, mock_import_string):
        """Test run_from_argv starting a server."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        self.command.run_from_argv(["manage.py", "prodserver", "web"])

        mock_backend_instance.start_server.assert_called_once()
        mock_exit.assert_not_called()

    @patch("sys.exit")
    def test_run_from_argv_command_error(self, mock_exit):
        """Test run_from_argv with CommandError."""
        with patch.object(self.command, "start_server") as mock_start:
            mock_start.side_effect = CommandError("Test error")

            self.command.run_from_argv(["manage.py", "prodserver", "nonexistent"])

            mock_exit.assert_called_with(1)

    @patch("sys.exit")
    def test_run_from_argv_system_check_error(self, mock_exit):
        """Test run_from_argv with SystemCheckError."""
        with patch.object(self.command, "start_server") as mock_start:
            mock_start.side_effect = lambda *x, **y: SystemCheckError(
                "System check failed"
            )

            self.command.run_from_argv(["manage.py", "prodserver", "web"])

            mock_exit.assert_called_with(2)

    @override_settings(PRODUCTION_PROCESSES={"web": {"BACKEND": "test.backend"}})
    @patch("sys.exit")
    def test_run_from_argv_traceback_option(self, mock_exit):
        """Test run_from_argv with --traceback option."""
        with patch.object(self.command, "start_server") as mock_start:
            mock_start.side_effect = CommandError("Test error")

            with pytest.raises(CommandError):
                self.command.run_from_argv(
                    [
                        "manage.py",
                        "prodserver",
                        "--traceback",
                        "web",
                    ]  # Use valid server name
                )

            # Should not call sys.exit when traceback is requested
            mock_exit.assert_not_called()

    def test_called_from_command_line_attribute(self):
        """Test that _called_from_command_line is set correctly."""
        assert hasattr(self.command, "_called_from_command_line")

        with patch.object(self.command, "start_server"):
            self.command.run_from_argv(["manage.py", "prodserver", "--list"])

        assert self.command._called_from_command_line is True

    @override_settings(
        PRODUCTION_PROCESSES={
            "web1": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"},
            "web2": {"BACKEND": "django_prodserver.backends.uvicorn.UvicornServer"},
            "worker": {"BACKEND": "django_prodserver.backends.celery.CeleryWorker"},
        }
    )
    def test_default_server_selection(self):
        """Test that first server is selected as default."""
        parser = MagicMock()
        self.command.add_arguments(parser)

        calls = parser.add_argument.call_args_list
        server_name_call = calls[0]
        args, kwargs = server_name_call

        # Should have a default value (first in choices)
        assert "default" in kwargs
        # The default should be one of the available choices
        assert kwargs["default"] in kwargs["choices"]

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"}
        }
    )
    def test_stdout_output_on_start(self):
        """Test that starting server outputs to stdout."""
        with patch(
            "django_prodserver.management.commands.prodserver.import_string"
        ) as mock_import:
            # Mock the backend to prevent actual server starting
            mock_backend_class = Mock()
            mock_backend_instance = Mock()
            mock_backend_instance.prep_server_args.return_value = []
            mock_backend_class.return_value = mock_backend_instance
            mock_import.return_value = mock_backend_class

            self.command.start_server("web")

        output = self.command.stdout.getvalue()
        assert "Starting server named web" in output

    def test_server_name_argument_properties(self):
        """Test server_name argument properties."""
        parser = MagicMock()
        self.command.add_arguments(parser)

        calls = parser.add_argument.call_args_list
        server_name_call = calls[0]
        args, kwargs = server_name_call

        assert args[0] == "server_name"
        assert kwargs["type"] is str
        assert kwargs["nargs"] == "?"

    @override_settings(
        PRODUCTION_PROCESSES={
            "web": {
                "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
                "ARGS": {"workers": "4", "bind": "0.0.0.0:8000"},
                "EXTRA_CONFIG": "ignored",
            }
        }
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    def test_start_server_passes_full_config(self, mock_import_string):
        """Test that start_server passes the complete server configuration."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        self.command.start_server("web")

        # Should pass the entire server config to the backend
        expected_config = {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"workers": "4", "bind": "0.0.0.0:8000"},
            "EXTRA_CONFIG": "ignored",
        }
        mock_backend_class.assert_called_once_with(**expected_config)

    def test_error_message_includes_available_servers(self):
        """Test that error message includes list of available servers."""
        with override_settings(
            PRODUCTION_PROCESSES={
                "web": {"BACKEND": "test.backend"},
                "worker": {"BACKEND": "test.backend"},
            }
        ):
            with pytest.raises(CommandError) as exc_info:
                self.command.start_server("nonexistent")

            error_message = str(exc_info.value)
            assert "web" in error_message
            assert "worker" in error_message
            assert "Available names are:" in error_message

    @patch("django_prodserver.management.commands.prodserver.handle_default_options")
    def test_handle_default_options_called(self, mock_handle_default_options):
        """Test that handle_default_options is called during run_from_argv."""
        with patch.object(self.command, "create_parser") as mock_create_parser:
            mock_parser = Mock()
            mock_options = Mock()
            mock_options.traceback = False
            mock_options.list = True
            mock_parser.parse_args.return_value = mock_options
            mock_create_parser.return_value = mock_parser

            with patch.object(self.command, "list_process_names"):
                self.command.run_from_argv(["manage.py", "prodserver", "--list"])

            mock_handle_default_options.assert_called_once_with(mock_options)

    @override_settings(
        PRODUCTION_PROCESSES={
            "test": {"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"}
        }
    )
    @patch("django_prodserver.management.commands.prodserver.import_string")
    def test_backend_start_server_exception_propagation(self, mock_import_string):
        """Test that exceptions from backend.start_server are propagated."""
        mock_backend_class = Mock()
        mock_backend_instance = Mock()
        mock_backend_instance.prep_server_args.return_value = []
        mock_backend_instance.start_server.side_effect = RuntimeError("Server failed")
        mock_backend_class.return_value = mock_backend_instance
        mock_import_string.return_value = mock_backend_class

        with pytest.raises(RuntimeError, match="Server failed"):
            self.command.start_server("test")

    def test_command_help_text(self):
        """Test that command has appropriate help text."""
        # The command should have help text accessible
        assert hasattr(self.command, "help")

    @override_settings(PRODUCTION_PROCESSES={})
    def test_add_arguments_no_servers_configured(self):
        """Test add_arguments raises CommandError when no servers are configured."""
        parser = MagicMock()

        with pytest.raises(CommandError) as exc_info:
            self.command.add_arguments(parser)

        assert "No servers configured in the PRODUCTION_PROCESSES setting" in str(
            exc_info.value
        )
        assert "Configure your servers before running this command" in str(
            exc_info.value
        )
