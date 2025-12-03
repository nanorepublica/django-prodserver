(backend-uvicorn)=

# Uvicorn

Fast ASGI server for async Django apps. Supports WebSockets and async views.

**Use when:** Async Django (3.1+), WebSockets
**Don't use when:** Traditional sync apps without async needs (use {ref}`backend-gunicorn`)

## Installation

```bash
pip install django-prodserver[uvicorn]

# For better performance
pip install uvicorn[standard]
```

## Backends

(backend-uvicorn-asgi)=

### ASGI Mode

For async Django with WebSocket support:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }
    }
}
```

(backend-uvicorn-wsgi)=

### WSGI Mode

For traditional Django with Uvicorn performance:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornWSGIServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
        }
    }
}
```

## Common ARGS

| Argument             | Default     | Description                   |
| -------------------- | ----------- | ----------------------------- |
| `host`               | `127.0.0.1` | Host to bind                  |
| `port`               | `8000`      | Port to bind                  |
| `workers`            | `1`         | Worker processes              |
| `loop`               | `auto`      | Event loop (`auto`, `uvloop`) |
| `log-level`          | `info`      | Log level                     |
| `no-access-log`      | `False`     | Disable access logging        |
| `proxy-headers`      | `False`     | Trust proxy headers           |
| `timeout-keep-alive` | `5`         | Keep-alive timeout            |
| `limit-concurrency`  | `None`      | Max concurrent connections    |
| `limit-max-requests` | `None`      | Restart after N requests      |

## Examples

### Production

```python
"ARGS": {
    "host": "0.0.0.0",
    "port": "8000",
    "workers": "4",
    "loop": "uvloop",
    "no-access-log": "True",
}
```

### Behind Reverse Proxy

```python
"ARGS": {
    "host": "127.0.0.1",
    "port": "8000",
    "proxy-headers": "True",
    "forwarded-allow-ips": "*",
}
```

### WebSocket Support

```python
"ARGS": {
    "host": "0.0.0.0",
    "port": "8000",
    "timeout-keep-alive": "60",
}
```

## ASGI vs WSGI

| Feature            | ASGI | WSGI |
| ------------------ | ---- | ---- |
| Async views        | Yes  | No   |
| WebSockets         | Yes  | No   |
| Traditional Django | Yes  | Yes  |

## Troubleshooting

**ASGI app not found:** Ensure `asgi.py` exists with `application` defined

**No async support:** Use ASGI backend, not WSGI

## Links

- [Uvicorn Docs](https://www.uvicorn.org/)
- [Settings](https://www.uvicorn.org/settings/)
