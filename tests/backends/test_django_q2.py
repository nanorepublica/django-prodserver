import sys
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from django_prodserver.backends.django_q2 import DjangoQ2Worker


class TestDjangoQ2WorkerImportErrors:
    """Tests for DjangoQ2Worker import error handling."""

    def test_import_error_handling_django_q2_not_installed(self):
        """Test graceful handling when django-q2 package not installed."""
        # Mock the import to fail
        with patch.dict(sys.modules, {"django_q": None}):
            with patch("builtins.__import__") as mock_import:
                original_import = __import__

                def side_effect(name, *args, **kwargs):
                    if name == "django_q":
                        raise ImportError("No module named 'django_q'")
                    return original_import(name, *args, **kwargs)

                mock_import.side_effect = side_effect

                with pytest.raises(ImproperlyConfigured) as exc_info:
                    DjangoQ2Worker()

                error_msg = str(exc_info.value)
                assert (
                    "django-q2 is required to use DjangoQ2Worker backend" in error_msg
                )
                assert "pip install django-q2" in error_msg

    def test_missing_installed_apps_error(self):
        """Test error when django_q not in INSTALLED_APPS."""
        # Create a mock django_q module
        mock_django_q = Mock()

        with patch.dict(sys.modules, {"django_q": mock_django_q}):
            with patch("django.conf.settings") as mock_settings:
                mock_settings.INSTALLED_APPS = ["django_prodserver"]  # Missing django_q

                with pytest.raises(ImproperlyConfigured) as exc_info:
                    DjangoQ2Worker()

                error_msg = str(exc_info.value)
                assert "Add 'django_q' to INSTALLED_APPS" in error_msg
                assert "django-q2.readthedocs.io" in error_msg

    def test_import_error_chain_preservation(self):
        """Test that the original ImportError is preserved in the exception chain."""
        original_error = ImportError("No module named 'django_q'")

        with patch.dict(sys.modules, {"django_q": None}):
            with patch("builtins.__import__") as mock_import:
                original_import = __import__

                def side_effect(name, *args, **kwargs):
                    if name == "django_q":
                        raise original_error
                    return original_import(name, *args, **kwargs)

                mock_import.side_effect = side_effect

                with pytest.raises(ImproperlyConfigured) as exc_info:
                    DjangoQ2Worker()

                # Check that the original exception is chained
                assert exc_info.value.__cause__ is original_error

    def test_installed_apps_check_case_sensitivity(self):
        """Test that INSTALLED_APPS check is case sensitive."""
        mock_django_q = Mock()

        with patch.dict(sys.modules, {"django_q": mock_django_q}):
            with patch("django.conf.settings") as mock_settings:
                # Test with wrong case
                mock_settings.INSTALLED_APPS = [
                    "django_prodserver",
                    "Django_Q",
                ]  # Wrong case

                with pytest.raises(ImproperlyConfigured) as exc_info:
                    DjangoQ2Worker()

                assert "Add 'django_q' to INSTALLED_APPS" in str(exc_info.value)

    def test_installed_apps_partial_match(self):
        """Test that INSTALLED_APPS check requires exact match."""
        mock_django_q = Mock()

        with patch.dict(sys.modules, {"django_q": mock_django_q}):
            with patch("django.conf.settings") as mock_settings:
                # Test with partial match
                mock_settings.INSTALLED_APPS = [
                    "django_prodserver",
                    "django_q_extra",
                ]  # Not exact

                with pytest.raises(ImproperlyConfigured) as exc_info:
                    DjangoQ2Worker()

                assert "Add 'django_q' to INSTALLED_APPS" in str(exc_info.value)


class TestDjangoQ2WorkerFunctionality:
    """Tests for DjangoQ2Worker functionality with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for all tests in this class."""
        self.mock_django_q = Mock()
        self.patcher_modules = patch.dict(sys.modules, {"django_q": self.mock_django_q})
        self.patcher_settings = patch("django.conf.settings")

        self.patcher_modules.start()
        self.mock_settings = self.patcher_settings.start()
        self.mock_settings.INSTALLED_APPS = ["django_prodserver", "django_q"]

        yield

        self.patcher_settings.stop()
        self.patcher_modules.stop()

    def test_init_without_args(self):
        """Test DjangoQ2Worker initialization without args."""
        worker = DjangoQ2Worker()
        assert worker.args == []

    def test_init_with_args(self):
        """Test DjangoQ2Worker initialization with args."""
        worker = DjangoQ2Worker(ARGS={"verbosity": "2", "cluster-name": "worker"})
        assert worker.args == ["--verbosity=2", "--cluster-name=worker"]

    def test_init_with_empty_args(self):
        """Test DjangoQ2Worker initialization with empty ARGS dict."""
        worker = DjangoQ2Worker(ARGS={})
        assert worker.args == []

    def test_init_with_complex_args(self):
        """Test DjangoQ2Worker initialization with complex ARGS."""
        worker = DjangoQ2Worker(
            ARGS={
                "verbosity": "2",
                "cluster-name": "high-priority",
                "settings": "myproject.settings.production",
                "run-once": "True",
            }
        )

        expected_args = [
            "--verbosity=2",
            "--cluster-name=high-priority",
            "--settings=myproject.settings.production",
            "--run-once=True",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in worker.args

        assert len(worker.args) == 4

    @patch("django.core.management.call_command")
    def test_start_server(self, mock_call_command):
        """Test start_server method."""
        worker = DjangoQ2Worker()
        args = ["--verbosity", "2", "--cluster-name", "test-cluster"]

        worker.start_server(*args)

        mock_call_command.assert_called_once_with("qcluster", *args)

    @patch("django.core.management.call_command")
    def test_start_server_no_args(self, mock_call_command):
        """Test start_server method with no args."""
        worker = DjangoQ2Worker()

        worker.start_server()

        mock_call_command.assert_called_once_with("qcluster")

    def test_prep_server_args(self):
        """Test prep_server_args method."""
        worker = DjangoQ2Worker(ARGS={"verbosity": "1"})
        args = worker.prep_server_args()
        assert args == ["--verbosity=1"]

    def test_prep_server_args_empty(self):
        """Test prep_server_args with no args."""
        worker = DjangoQ2Worker()
        args = worker.prep_server_args()
        assert args == []

    def test_inheritance_from_base_backend(self):
        """Test that DjangoQ2Worker properly inherits from BaseServerBackend."""
        from django_prodserver.backends.base import BaseServerBackend

        worker = DjangoQ2Worker()
        assert isinstance(worker, BaseServerBackend)

    @patch("django.core.management.call_command")
    def test_start_server_with_various_args(self, mock_call_command):
        """Test start_server with various argument types."""
        worker = DjangoQ2Worker()
        args = ["--verbosity=2", "--cluster-name=test", "--run-once"]

        worker.start_server(*args)

        mock_call_command.assert_called_once_with("qcluster", *args)

    @patch("django.core.management.call_command")
    def test_start_server_single_arg(self, mock_call_command):
        """Test start_server with a single argument."""
        worker = DjangoQ2Worker()

        worker.start_server("--verbosity=3")

        mock_call_command.assert_called_once_with("qcluster", "--verbosity=3")

    @patch("django.core.management.call_command")
    def test_full_workflow(self, mock_call_command):
        """Test the complete workflow from initialization to server start."""
        worker = DjangoQ2Worker(ARGS={"verbosity": "1", "cluster-name": "worker"})
        prepared_args = worker.prep_server_args()
        worker.start_server(*prepared_args)

        mock_call_command.assert_called_once_with(
            "qcluster", "--verbosity=1", "--cluster-name=worker"
        )

    @patch("django.core.management.call_command")
    def test_management_command_exception_propagation(self, mock_call_command):
        """Test that management command exceptions are properly propagated."""
        mock_call_command.side_effect = RuntimeError("qcluster command failed")

        worker = DjangoQ2Worker()

        with pytest.raises(RuntimeError, match="qcluster command failed"):
            worker.start_server("--verbosity=2")

        mock_call_command.assert_called_once_with("qcluster", "--verbosity=2")

    @patch("django.core.management.call_command")
    def test_management_command_import_error_propagation(self, mock_call_command):
        """Test that import errors from management are properly propagated."""
        from django.core.management import CommandError

        mock_call_command.side_effect = CommandError("Unknown command: qcluster")

        worker = DjangoQ2Worker()

        with pytest.raises(CommandError, match="Unknown command: qcluster"):
            worker.start_server()

        mock_call_command.assert_called_once_with("qcluster")

    def test_server_args_formatting_special_characters(self):
        """Test that server args with special characters are properly formatted."""
        worker = DjangoQ2Worker(
            ARGS={
                "cluster-name": "worker-with-dashes",
                "log-level": "DEBUG",
                "settings": "myproject.settings.local",
            }
        )

        expected_args = [
            "--cluster-name=worker-with-dashes",
            "--log-level=DEBUG",
            "--settings=myproject.settings.local",
        ]

        # Check all expected args are present
        for expected_arg in expected_args:
            assert expected_arg in worker.args

        assert len(worker.args) == 3

    def test_init_with_extra_config_keys(self):
        """Test that extra configuration keys are ignored properly."""
        worker = DjangoQ2Worker(
            ARGS={"verbosity": "1"},
            EXTRA_CONFIG={"key": "ignored"},
            ANOTHER_KEY={"number": "123"},
        )

        # Should only process ARGS
        assert worker.args == ["--verbosity=1"]

    @patch("django.core.management.call_command")
    def test_start_server_empty_string_args(self, mock_call_command):
        """Test start_server with empty string arguments."""
        worker = DjangoQ2Worker()

        worker.start_server("", "--verbosity=1", "")

        mock_call_command.assert_called_once_with("qcluster", "", "--verbosity=1", "")

    def test_qcluster_command_name_constant(self):
        """Test that the qcluster command name is consistent."""
        worker = DjangoQ2Worker()

        with patch("django.core.management.call_command") as mock_call_command:
            worker.start_server("--test")

            # Verify the command name is always "qcluster"
            args, kwargs = mock_call_command.call_args
            assert args[0] == "qcluster"

    @patch("django.core.management.call_command")
    def test_start_server_with_kwargs_ignored(self, mock_call_command):
        """Test that start_server only accepts positional args."""
        worker = DjangoQ2Worker()

        # start_server signature only accepts *args, no **kwargs
        worker.start_server("--verbosity=2", "--cluster-name=test")

        mock_call_command.assert_called_once_with(
            "qcluster", "--verbosity=2", "--cluster-name=test"
        )

    def test_args_property_immutable_after_init(self):
        """Test that args property reflects initialization state."""
        worker = DjangoQ2Worker(ARGS={"verbosity": "2"})
        original_args = worker.args.copy()

        # Args should be the same after calling other methods
        worker.prep_server_args()

        assert worker.args == original_args

    def test_successful_initialization_with_all_requirements(self):
        """Test successful initialization when all requirements are met."""
        self.mock_settings.INSTALLED_APPS = [
            "django_prodserver",
            "django_q",
            "other_app",
        ]

        # Should not raise any exceptions
        worker = DjangoQ2Worker(ARGS={"verbosity": "2"})

        assert worker is not None
        assert worker.args == ["--verbosity=2"]

    def test_django_q_in_installed_apps_different_positions(self):
        """Test that django_q is found regardless of position in INSTALLED_APPS."""
        # Test django_q at the beginning
        self.mock_settings.INSTALLED_APPS = ["django_q", "django_prodserver", "other"]
        worker1 = DjangoQ2Worker()
        assert worker1 is not None

        # Test django_q in the middle
        self.mock_settings.INSTALLED_APPS = ["django_prodserver", "django_q", "other"]
        worker2 = DjangoQ2Worker()
        assert worker2 is not None

        # Test django_q at the end
        self.mock_settings.INSTALLED_APPS = ["django_prodserver", "other", "django_q"]
        worker3 = DjangoQ2Worker()
        assert worker3 is not None

    @patch("django.core.management.call_command")
    def test_django_q2_specific_args(self, mock_call_command):
        """Test Django-Q2 specific arguments are handled correctly."""
        worker = DjangoQ2Worker(
            ARGS={
                "cluster-name": "my-cluster",
                "run-once": "True",
                "verbosity": "3",
            }
        )

        # Use prepared args to start server (proper workflow)
        prepared_args = worker.prep_server_args()
        worker.start_server(*prepared_args)

        # Check that Django-Q2 specific args are passed correctly
        call_args = mock_call_command.call_args[0]
        assert call_args[0] == "qcluster"

        remaining_args = call_args[1:]
        assert "--cluster-name=my-cluster" in remaining_args
        assert "--run-once=True" in remaining_args
        assert "--verbosity=3" in remaining_args

    def test_proper_exception_types(self):
        """Test that the correct exception types are raised."""
        # Test missing INSTALLED_APPS -> ImproperlyConfigured
        self.mock_settings.INSTALLED_APPS = []

        with pytest.raises(ImproperlyConfigured):
            DjangoQ2Worker()
