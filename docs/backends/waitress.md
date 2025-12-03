(backend-waitress)=

# Waitress

Pure Python WSGI server with excellent Windows support. No compilation required.

**Use when:** Windows deployments, pure Python environments
**Don't use when:** Need async/WebSockets (use {ref}`backend-uvicorn-asgi`)

## Installation

```bash
pip install django-prodserver[waitress]
```

## Configuration

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "threads": "4",
        }
    }
}
```

## Common ARGS

| Argument            | Default   | Description                    |
| ------------------- | --------- | ------------------------------ |
| `host`              | `0.0.0.0` | Host to bind                   |
| `port`              | `8080`    | Port to bind                   |
| `threads`           | `4`       | Thread count                   |
| `channel-timeout`   | `120`     | Channel timeout (seconds)      |
| `connection-limit`  | `100`     | Max simultaneous connections   |
| `backlog`           | `1024`    | Socket backlog                 |
| `unix-socket`       | `None`    | Unix socket path (Linux/macOS) |
| `expose-tracebacks` | `False`   | Show tracebacks (dev only)     |

## Examples

### Production

```python
"ARGS": {
    "host": "0.0.0.0",
    "port": "8000",
    "threads": "8",
    "connection-limit": "500",
    "channel-timeout": "120",
}
```

### Windows

```python
"ARGS": {
    "host": "0.0.0.0",
    "port": "8000",
    "threads": "6",
}
```

### Unix Socket

```python
"ARGS": {
    "unix-socket": "/var/run/myapp.sock",
    "threads": "4",
}
```

## Thread Count

- **Low traffic:** 2-4 threads
- **Medium traffic:** 4-8 threads
- **High traffic:** 8-16 threads

## Troubleshooting

**Slow responses:** Increase `threads` and `channel-timeout`

**Connection refused under load:** Increase `connection-limit` and `backlog`

## Links

- [Waitress Docs](https://docs.pylonsproject.org/projects/waitress/)
- [Arguments](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html)
