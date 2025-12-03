(backend-gunicorn)=

# Gunicorn

Industry-standard WSGI server for Django. Battle-tested and widely deployed.

**Use when:** Traditional Django apps on Linux
**Don't use when:** Windows (use {ref}`backend-waitress`), async/WebSockets (use {ref}`backend-uvicorn-asgi`)

## Installation

```bash
pip install django-prodserver[gunicorn]
```

## Configuration

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "timeout": "60",
        }
    }
}
```

## Common ARGS

| Argument              | Default          | Description                                |
| --------------------- | ---------------- | ------------------------------------------ |
| `bind`                | `127.0.0.1:8000` | Socket to bind (host:port or unix socket)  |
| `workers`             | `1`              | Worker processes (recommend: `2-4 x CPU`)  |
| `worker-class`        | `sync`           | Worker type (`sync`, `gevent`, `eventlet`) |
| `timeout`             | `30`             | Request timeout (seconds)                  |
| `max-requests`        | `0`              | Restart workers after N requests           |
| `max-requests-jitter` | `0`              | Random jitter for max-requests             |
| `keepalive`           | `2`              | Keep-alive timeout                         |
| `accesslog`           | `None`           | Access log path (`-` for stdout)           |
| `errorlog`            | `stderr`         | Error log path                             |
| `loglevel`            | `info`           | Log level                                  |

## Examples

### Production

```python
"ARGS": {
    "bind": "0.0.0.0:8000",
    "workers": "8",
    "worker-class": "gevent",
    "timeout": "120",
    "max-requests": "1000",
    "max-requests-jitter": "100",
}
```

### Unix Socket (behind nginx)

```python
"ARGS": {
    "bind": "unix:/var/run/myapp.sock",
    "workers": "4",
    "user": "www-data",
}
```

### Gevent (I/O-bound apps)

```bash
pip install gunicorn[gevent]
```

```python
"ARGS": {
    "worker-class": "gevent",
    "worker-connections": "1000",
    "workers": "4",
}
```

## Worker Count

Formula: `(2 x CPU_cores) + 1`

- **CPU-bound:** Fewer workers (1-2 per core)
- **I/O-bound:** More workers or use gevent

## Troubleshooting

**Worker timeout:** Increase `timeout` or investigate slow requests

**High memory:** Reduce workers, add `max-requests` for recycling

**Port in use:** Change port or stop conflicting process

## Links

- [Gunicorn Docs](https://docs.gunicorn.org/)
- [Settings Reference](https://docs.gunicorn.org/en/stable/settings.html)
