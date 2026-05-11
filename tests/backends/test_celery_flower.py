import sys
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured

from django_prodserver.backends.workers.celery import CeleryFlower


class TestCeleryFlowerImportErrors:
    """Tests for CeleryFlower import error handling."""

    def test_import_error_when_flower_not_installed(self):
        """Test ImproperlyConfigured is raised when flower is not installed."""
        with patch.dict(sys.modules, {"flower": None}):
            original_import = __import__

            def side_effect(name, *args, **kwargs):
                if name == "flower":
                    raise ImportError("No module named 'flower'")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=side_effect):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    CeleryFlower(APP="myproject.celery.app")

        error_msg = str(exc_info.value)
        assert "flower is required to use the CeleryFlower backend" in error_msg
        assert "pip install django-prodserver[flower]" in error_msg

    def test_import_error_chain_preserved(self):
        """Test that the original ImportError is preserved in the exception chain."""
        original_error = ImportError("No module named 'flower'")

        with patch.dict(sys.modules, {"flower": None}):
            original_import = __import__

            def side_effect(name, *args, **kwargs):
                if name == "flower":
                    raise original_error
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=side_effect):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    CeleryFlower(APP="myproject.celery.app")

        assert exc_info.value.__cause__ is original_error


class TestCeleryFlower:
    """Tests for CeleryFlower functionality with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def mock_flower_module(self):
        """Provide a stub ``flower`` module so the import check passes."""
        with patch.dict(sys.modules, {"flower": Mock()}):
            yield

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_with_app(self, mock_import_string):
        """Test CeleryFlower initialization with APP config."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        server_config = {
            "BACKEND": "django_prodserver.backends.workers.celery.CeleryFlower",
            "APP": "myproject.celery.app",
            "ARGS": {"port": "5555", "address": "0.0.0.0"},
        }

        flower = CeleryFlower(**server_config)

        assert flower.app == mock_app
        assert flower.args == ["--port=5555", "--address=0.0.0.0"]
        mock_import_string.assert_called_once_with("myproject.celery.app")

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_init_without_args(self, mock_import_string):
        """Test CeleryFlower initialization without ARGS."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        flower = CeleryFlower(APP="myproject.celery.app")

        assert flower.app == mock_app
        assert flower.args == []

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server(self, mock_import_string):
        """Test start_server dispatches the flower subcommand on the celery app."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        flower = CeleryFlower(APP="myproject.celery.app")
        flower.start_server("--port=5555", "--address=0.0.0.0")

        mock_app.start.assert_called_once_with(
            argv=["flower", "--port=5555", "--address=0.0.0.0"]
        )

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_no_args(self, mock_import_string):
        """Test start_server with no args."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        flower = CeleryFlower(APP="myproject.celery.app")
        flower.start_server()

        mock_app.start.assert_called_once_with(argv=["flower"])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_full_workflow(self, mock_import_string):
        """Test the complete workflow from initialization to server start."""
        mock_app = Mock()
        mock_import_string.return_value = mock_app

        flower = CeleryFlower(APP="myproject.celery.app", ARGS={"port": "5555"})
        flower.start_server(*flower.prep_server_args())

        mock_app.start.assert_called_once_with(argv=["flower", "--port=5555"])

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_inheritance(self, mock_import_string):
        """Test that CeleryFlower inherits from CeleryWorker / BaseWorkerBackend."""
        from django_prodserver.backends.base import BaseWorkerBackend
        from django_prodserver.backends.workers.celery import CeleryWorker

        mock_import_string.return_value = Mock()
        flower = CeleryFlower(APP="myproject.celery.app")

        assert isinstance(flower, CeleryWorker)
        assert isinstance(flower, BaseWorkerBackend)

    @patch("django_prodserver.backends.workers.celery.import_string")
    def test_start_server_exception_propagation(self, mock_import_string):
        """Test that exceptions from app.start are propagated."""
        mock_app = Mock()
        mock_app.start.side_effect = RuntimeError("flower failed to start")
        mock_import_string.return_value = mock_app

        flower = CeleryFlower(APP="myproject.celery.app")

        with pytest.raises(RuntimeError, match="flower failed to start"):
            flower.start_server()
