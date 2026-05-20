"""
Tests for the deprecated `prodserver` management command alias.

The full behavioral coverage lives in `tests/test_server_command.py`. The
tests here verify that the deprecated alias still works AND emits a
`DeprecationWarning` so users have a clear migration signal.
"""

import warnings
from io import StringIO
from unittest.mock import patch

from django.test import TestCase, override_settings

from django_prodserver.management.commands.prodserver import (
    DEPRECATION_MESSAGE,
)
from django_prodserver.management.commands.prodserver import (
    Command as ProdServerCommand,
)
from django_prodserver.management.commands.server import Command as ServerCommand
from tests.test_server_command import DUMMY_SERVER, _DummyServerBackend


class TestProdserverDeprecation(TestCase):
    """The `prodserver` command must keep working but warn loudly."""

    def setUp(self):
        self.command = ProdServerCommand()
        self.command.stdout = StringIO()
        self.command.stderr = StringIO()

    def test_prodserver_is_subclass_of_server(self):
        """The deprecated alias must inherit all behavior from `server`."""
        assert issubclass(ProdServerCommand, ServerCommand)

    def test_command_instance_creation(self):
        assert isinstance(self.command, ProdServerCommand)

    @override_settings(PRODUCTION_PROCESSES={"web": {"BACKEND": DUMMY_SERVER}})
    def test_run_from_argv_emits_deprecation_warning(self):
        """Running `prodserver --list` must raise a DeprecationWarning."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.command.run_from_argv(["manage.py", "prodserver", "--list"])

        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecations) == 1
        assert "prodserver" in str(deprecations[0].message)
        assert "server" in str(deprecations[0].message)

    @override_settings(PRODUCTION_PROCESSES={"web": {"BACKEND": DUMMY_SERVER}})
    def test_run_from_argv_writes_warning_to_stderr(self):
        """The deprecation must also be visible to humans on stderr."""
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            self.command.run_from_argv(["manage.py", "prodserver", "--list"])

        assert "DeprecationWarning" in self.command.stderr.getvalue()
        assert "prodserver" in self.command.stderr.getvalue()

    @override_settings(PRODUCTION_PROCESSES={"web": {"BACKEND": DUMMY_SERVER}})
    def test_run_from_argv_still_starts_server(self):
        """Despite the warning, the command must still start the server."""
        with (
            warnings.catch_warnings(),
            patch.object(_DummyServerBackend, "start_server") as mock_start,
        ):
            warnings.simplefilter("always")
            self.command.run_from_argv(["manage.py", "prodserver", "web"])

        mock_start.assert_called_once()

    def test_deprecation_message_mentions_removal_version(self):
        """The deprecation message must point users to `server` and 4.0.0."""
        assert "server" in DEPRECATION_MESSAGE
        assert "4.0.0" in DEPRECATION_MESSAGE
        assert "prodserver" in DEPRECATION_MESSAGE
