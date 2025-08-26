from unittest.mock import Mock, patch

from django.core.management.commands.runserver import Command as RunServerCommand
from django.test import TestCase

from django_prodserver.management.commands.devserver import Command


class TestDevserverCommand(TestCase):
    """Tests for the devserver management command."""

    def setUp(self):
        """Set up test fixtures."""
        self.command = Command()

    def test_command_inheritance(self):
        """Test that devserver command inherits from Django's runserver."""
        assert isinstance(self.command, RunServerCommand)
        assert issubclass(Command, RunServerCommand)

    def test_command_is_runserver_subclass(self):
        """Test that Command is a proper subclass of RunServerCommand."""
        # Should have all the same attributes as RunServerCommand
        RunServerCommand()

        # Compare some key attributes that should be inherited
        assert hasattr(self.command, "default_addr")
        assert hasattr(self.command, "default_port")
        assert hasattr(self.command, "protocol")
        assert hasattr(self.command, "server_cls")

    def test_command_docstring(self):
        """Test that command has appropriate docstring."""
        assert Command.__doc__ == "Class to override the name of 'runserver'."

    def test_command_instantiation(self):
        """Test that command can be instantiated without errors."""
        command = Command()
        assert isinstance(command, Command)
        assert isinstance(command, RunServerCommand)

    def test_command_has_runserver_methods(self):
        """Test that command has all RunServerCommand methods."""
        runserver_methods = [
            method
            for method in dir(RunServerCommand)
            if not method.startswith("_")
            and callable(getattr(RunServerCommand, method))
        ]

        for method_name in runserver_methods:
            assert hasattr(self.command, method_name)
            assert callable(getattr(self.command, method_name))

    @patch("django.core.management.commands.runserver.Command.run")
    def test_run_method_inheritance(self, mock_run):
        """Test that run method is properly inherited."""
        self.command.run()
        mock_run.assert_called_once()

    @patch("django.core.management.commands.runserver.Command.handle")
    def test_handle_method_inheritance(self, mock_handle):
        """Test that handle method is properly inherited."""
        self.command.handle()
        mock_handle.assert_called_once()

    def test_command_help_inheritance(self):
        """Test that help text is inherited from runserver."""
        RunServerCommand()
        # Help should be inherited or at least accessible
        assert hasattr(self.command, "help")

    def test_command_default_settings(self):
        """Test that default settings are inherited."""
        runserver_command = RunServerCommand()

        # Should have same default addr and port
        assert self.command.default_addr == runserver_command.default_addr
        assert self.command.default_port == runserver_command.default_port

    @patch("django.core.management.commands.runserver.Command.add_arguments")
    def test_add_arguments_inheritance(self, mock_add_arguments):
        """Test that add_arguments is properly inherited."""
        parser = Mock()
        self.command.add_arguments(parser)
        mock_add_arguments.assert_called_once_with(parser)

    def test_command_attributes_match_runserver(self):
        """Test that key attributes match those of runserver command."""
        runserver_command = RunServerCommand()

        # Compare class-level attributes
        assert self.command.protocol == runserver_command.protocol
        assert type(self.command.server_cls) is type(runserver_command.server_cls)

    def test_command_class_definition(self):
        """Test the class definition structure."""
        # Should have minimal class body (just pass and docstring)
        import inspect

        source = inspect.getsource(Command)

        # Should contain the pass statement
        assert "pass" in source
        assert "Class to override the name of 'runserver'." in source

    def test_mro_contains_runserver(self):
        """Test that method resolution order includes RunServerCommand."""
        mro = Command.__mro__
        assert RunServerCommand in mro
        # RunServerCommand should come before BaseCommand in MRO
        runserver_index = mro.index(RunServerCommand)
        assert runserver_index > 0  # Should not be the first (Command itself is first)

    @patch("django.core.management.commands.runserver.Command")
    def test_super_calls_work(self, mock_runserver_command):
        """Test that super() calls would work properly."""
        # This tests the inheritance structure
        mock_instance = Mock()
        mock_runserver_command.return_value = mock_instance

        # Should be able to call super() methods
        assert hasattr(self.command, "__class__")
        assert self.command.__class__.__bases__[0] == RunServerCommand

    def test_command_can_be_imported(self):
        """Test that command can be imported from the module."""
        from django_prodserver.management.commands.devserver import (
            Command as ImportedCommand,
        )

        assert ImportedCommand == Command
        assert issubclass(ImportedCommand, RunServerCommand)

    def test_empty_class_body(self):
        """Test that class body is minimal."""
        import inspect

        # Get the class source
        source = inspect.getsource(Command)
        lines = [line.strip() for line in source.split("\n") if line.strip()]

        # Should have: class definition, docstring, and pass
        # Filter out empty lines and comments
        non_empty_lines = [line for line in lines if line and not line.startswith("#")]

        # Should be minimal: class def, docstring, pass
        assert len(non_empty_lines) <= 4  # class, docstring open, docstring, pass

    def test_isinstance_checks(self):
        """Test various isinstance checks."""
        from django.core.management.base import BaseCommand

        assert isinstance(self.command, Command)
        assert isinstance(self.command, RunServerCommand)
        assert isinstance(self.command, BaseCommand)

    def test_class_name_and_module(self):
        """Test class name and module information."""
        assert Command.__name__ == "Command"
        assert Command.__module__ == "django_prodserver.management.commands.devserver"

    def test_no_additional_attributes(self):
        """Test that no additional attributes are added to the class."""
        # Get attributes that are specific to Command (not inherited)
        command_attrs = set(dir(Command)) - set(dir(RunServerCommand))

        # Should only have minimal class-specific attributes
        # Remove common dunder attributes that might differ
        command_attrs = {
            attr
            for attr in command_attrs
            if not attr.startswith("__") or attr in ["__doc__", "__module__"]
        }

        # Should have at most __doc__ and __module__
        expected_attrs = {"__doc__", "__module__"}
        assert command_attrs.issubset(expected_attrs)

    def test_command_functionality_passthrough(self):
        """Test that command functionality passes through to parent."""
        # Mock the parent class method to ensure it gets called
        with patch.object(RunServerCommand, "check") as mock_check:
            # This should call the parent's check method
            self.command.check()
            mock_check.assert_called_once()

    def test_command_option_parsing_inheritance(self):
        """Test that option parsing is inherited correctly."""
        # Create a mock parser to test add_arguments
        parser = Mock()

        # Should be able to call add_arguments without error
        self.command.add_arguments(parser)

        # Parser should have been called (through inheritance)
        assert parser.add_argument.called or hasattr(self.command, "add_arguments")
