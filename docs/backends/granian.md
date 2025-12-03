(backend-granian)=

# Granian

High-performance Rust-based server supporting both ASGI and WSGI.

**Use when:** Maximum performance, modern deployments
**Don't use when:** Need mature ecosystem (use {ref}`backend-gunicorn` or {ref}`backend-uvicorn-asgi`)

## Installation

```bash
pip install django-prodserver[granian]
```

## Backends

(backend-granian-asgi)=
### ASGI Mode

For async Django with WebSocket support:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }
    }
}
```

(backend-granian-wsgi)=
### WSGI Mode

For traditional Django:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }
    }
}
```

## Common ARGS

| Argument | Default | Description |
|----------|---------|-------------|
| `address` | `127.0.0.1` | Address to bind |
| `port` | `8000` | Port to bind |
| `workers` | `1` | Worker processes |
| `threads` | `1` | Threads per worker (WSGI) |
| `blocking-threads` | `1` | Blocking threads (ASGI) |
| `backlog` | `1024` | Connection backlog |
| `http` | `auto` | HTTP version (`auto`, `1`, `2`) |
| `log-level` | `info` | Log level |
| `log-access` | `True` | Enable access logging |
| `ssl-cert` | `None` | SSL certificate path |
| `ssl-key` | `None` | SSL key path |

## Examples

### High-Performance ASGI

```python
"ARGS": {
    "address": "0.0.0.0",
    "port": "8000",
    "workers": "4",
    "blocking-threads": "2",
    "log-access": "False",
}
```

### WSGI with Thread Pool

```python
"ARGS": {
    "address": "0.0.0.0",
    "port": "8000",
    "workers": "2",
    "threads": "4",
}
```

### HTTP/2

```python
"ARGS": {
    "http": "2",
    "workers": "4",
}
```

## ASGI vs WSGI

| Feature | ASGI | WSGI |
|---------|------|------|
| Async views | Yes | No |
| WebSockets | Yes | No |
| Thread model | Async + blocking | Thread pool |

## Troubleshooting

**Installation fails:** Granian requires Rust on some platforms. Try `pip install --upgrade granian`

**ASGI app not found:** Ensure `asgi.py` exists

## Links

- [Granian GitHub](https://github.com/emmett-framework/granian)
