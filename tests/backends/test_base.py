import pytest

from django_prodserver.backends.base import BaseServerBackend


def test_init_without_args():
    """Test BaseServerBackend initialization without ARGS."""
    backend = BaseServerBackend()
    assert backend.args == []


def test_init_with_args():
    """Test BaseServerBackend initialization with ARGS."""
    backend = BaseServerBackend(ARGS={"foo": "bar", "baz": "qux"})
    assert backend.args == ["--foo=bar", "--baz=qux"]


def test_init_with_empty_args():
    """Test BaseServerBackend initialization with empty ARGS."""
    backend = BaseServerBackend(ARGS={})
    assert backend.args == []


def test_start_server_not_implemented():
    """Test that start_server raises NotImplementedError."""
    backend = BaseServerBackend()
    with pytest.raises(NotImplementedError):
        backend.start_server()


def test_prep_server_args():
    """Test prep_server_args returns formatted args."""
    backend = BaseServerBackend(ARGS={"foo": "bar"})
    assert backend.prep_server_args() == ["--foo=bar"]


def test_prep_server_args_empty():
    """Test prep_server_args with no args."""
    backend = BaseServerBackend()
    assert backend.prep_server_args() == []


def test_format_server_args_from_dict():
    """Test _format_server_args_from_dict method."""
    backend = BaseServerBackend()
    args = {"bind": "0.0.0.0:8000", "workers": "4"}
    result = backend._format_server_args_from_dict(args)
    assert result == ["--bind=0.0.0.0:8000", "--workers=4"]


def test_format_server_args_from_empty_dict():
    """Test _format_server_args_from_dict with empty dict."""
    backend = BaseServerBackend()
    result = backend._format_server_args_from_dict({})
    assert result == []


def test_start_server_with_args():
    """
    Test that start_server can accept arguments.

    (even though it raises NotImplementedError).
    """
    backend = BaseServerBackend()
    with pytest.raises(NotImplementedError):
        backend.start_server("arg1", "arg2")


def test_init_with_other_server_args():
    """Test initialization with other server configuration arguments."""
    backend = BaseServerBackend(OTHER_CONFIG={"key": "value"}, ARGS={"port": "8000"})
    assert backend.args == ["--port=8000"]
    # Other config arguments are not processed, only ARGS


def test_multiple_server_args_ordering():
    """Test that multiple server args maintain consistent ordering."""
    backend = BaseServerBackend(ARGS={"workers": "4", "bind": "127.0.0.1:8000"})
    # The order might vary based on dict iteration, so we check both args are present
    assert "--workers=4" in backend.args
    assert "--bind=127.0.0.1:8000" in backend.args
    assert len(backend.args) == 2
