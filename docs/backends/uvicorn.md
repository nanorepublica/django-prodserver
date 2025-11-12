(backend-uvicorn)=

# Uvicorn

Uvicorn is a lightning-fast ASGI server built on uvloop and httptools. It's designed for async Python web applications and is the recommended server for async Django applications (Django 3.1+).

## Overview

Uvicorn provides both ASGI and WSGI interfaces, making it versatile for different types of Django applications:

- **Uvicorn ASGI** - For async Django apps with WebSocket and async view support
- **Uvicorn WSGI** - For traditional Django apps in WSGI compatibility mode

Both modes share the same excellent performance characteristics and configuration options.

## When to Use

**Choose Uvicorn when you need:**
- Async Django applications (Django 3.1+)
- WebSocket support
- Modern async/await views and middleware
- High-performance ASGI server
- Async ORM queries and third-party library support

**Consider alternatives if:**
- You don't use async features → Use {ref}`backend-gunicorn` for traditional WSGI
- You need maximum performance with Rust → Use {ref}`backend-granian-asgi`
- You're on Windows and want simplicity → Use {ref}`backend-waitress`

## Installation

Install Uvicorn via pip:

```bash
# Standard installation
pip install uvicorn

# With uvloop and httptools for better performance (recommended)
pip install uvicorn[standard]
```

For more installation options, see the [official Uvicorn documentation](https://www.uvicorn.org/).

(backend-uvicorn-asgi)=

## Uvicorn ASGI Mode

Use ASGI mode for async Django applications with WebSocket and async view support.

### Basic Configuration

#### Minimal Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
        }
    }
}
```

Start the server:
```bash
python manage.py prodserver web
```

#### Recommended Production Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "log-level": "info",
        }
    }
}
```

### ARGS Translation

The `ARGS` dictionary is translated to Uvicorn command-line arguments:

```python
"ARGS": {
    "host": "0.0.0.0",              # --host=0.0.0.0
    "port": "8000",                  # --port=8000
    "workers": "4",                  # --workers=4
    "log-level": "info",             # --log-level=info
}
```

This translates to:
```bash
uvicorn myproject.asgi:application --host=0.0.0.0 --port=8000 --workers=4 --log-level=info
```

(backend-uvicorn-wsgi)=

## Uvicorn WSGI Mode

Use WSGI mode for traditional Django applications when you want Uvicorn's performance without async features.

### Basic Configuration

```python
# settings.py
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

::::{note}
Uvicorn WSGI mode automatically adds `--interface=wsgi` to run in WSGI compatibility mode.
::::

## Configuration Reference

### Common ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `host` | string | `127.0.0.1` | The host to bind |
| `port` | integer | `8000` | The port to bind |
| `workers` | integer | `1` | Number of worker processes |
| `loop` | string | `auto` | Event loop implementation (`auto`, `asyncio`, `uvloop`) |
| `log-level` | string | `info` | Log level (`critical`, `error`, `warning`, `info`, `debug`, `trace`) |
| `access-log` / `no-access-log` | boolean | `True` | Enable/disable access logging |
| `use-colors` / `no-use-colors` | boolean | `True` | Enable/disable colored log output |
| `proxy-headers` | boolean | `False` | Enable X-Forwarded-Proto, X-Forwarded-For headers |
| `forwarded-allow-ips` | string | `None` | Comma-separated list of IPs to trust with proxy headers |

### SSL/TLS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `ssl-keyfile` | string | `None` | Path to SSL key file |
| `ssl-certfile` | string | `None` | Path to SSL certificate file |
| `ssl-keyfile-password` | string | `None` | SSL key file password |
| `ssl-version` | integer | `None` | SSL version (e.g., `2` for TLSv1.2) |
| `ssl-cert-reqs` | integer | `0` | Whether client certificate is required |
| `ssl-ca-certs` | string | `None` | Path to CA certificates file |

### Development Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `reload` | boolean | `False` | Enable auto-reload on code changes (development only) |
| `reload-dir` | string | Current dir | Directory to watch for reloads |
| `reload-include` | string | `*.py` | Files to watch for reloads (glob pattern) |
| `reload-exclude` | string | None | Files to exclude from reload watching |

### Performance Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `limit-concurrency` | integer | `None` | Maximum number of concurrent connections |
| `limit-max-requests` | integer | `None` | Maximum number of requests before worker restart |
| `backlog` | integer | `2048` | Maximum number of pending connections |
| `timeout-keep-alive` | integer | `5` | Keep-alive timeout (seconds) |

For complete options, see [Uvicorn Settings Documentation](https://www.uvicorn.org/settings/).

## Advanced Examples

### High-Performance ASGI Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "loop": "uvloop",
            "log-level": "warning",
            "no-access-log": "True",
            "limit-concurrency": "1000",
            "backlog": "2048",
        }
    }
}
```

**Configuration explanation:**
- `workers: 4` - Multiple processes for concurrency
- `loop: uvloop` - High-performance event loop
- `no-access-log: True` - Disable access logs for performance
- `limit-concurrency: 1000` - Cap concurrent connections

### Behind a Reverse Proxy

For use with nginx or another reverse proxy:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "workers": "4",
            "proxy-headers": "True",
            "forwarded-allow-ips": "*",
            "log-level": "info",
        }
    }
}
```

::::{warning}
Only use `forwarded-allow-ips: "*"` if your reverse proxy is properly configured. In production, specify exact IPs.
::::

### With SSL/TLS

Direct HTTPS serving (usually handled by reverse proxy instead):

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "443",
            "ssl-keyfile": "/path/to/key.pem",
            "ssl-certfile": "/path/to/cert.pem",
            "workers": "4",
        }
    }
}
```

### Development with Auto-Reload

```python
# settings_dev.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "reload": "True",
            "log-level": "debug",
            "reload-dir": ".",
        }
    }
}
```

::::{warning}
Never use `reload: True` in production - it impacts performance and stability.
::::

### WebSocket Support

For WebSocket applications:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "timeout-keep-alive": "60",  # Longer keep-alive for WebSockets
            "log-level": "info",
        }
    }
}
```

## ASGI vs WSGI Mode Comparison

| Feature | ASGI Mode | WSGI Mode |
|---------|-----------|-----------|
| **Async Views** | Yes | No |
| **WebSocket** | Yes | No |
| **Async ORM** | Yes | No |
| **Traditional Django** | Yes | Yes |
| **Performance** | High | High |
| **Use Case** | Modern async apps | Traditional apps with Uvicorn performance |

**When to use each:**
- **ASGI Mode:** Your app uses async views, WebSockets, or async ORM queries
- **WSGI Mode:** Traditional Django app, but you want Uvicorn's performance

## Worker Count Recommendations

Uvicorn uses an async event loop, so worker recommendations differ from traditional servers:

**Formula:** `1-2 workers per CPU core`

```python
import multiprocessing

workers = multiprocessing.cpu_count()

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": str(workers),
        }
    }
}
```

**Guidelines:**
- **Async apps:** Fewer workers needed due to event loop concurrency
- **I/O-bound:** Single worker can handle many concurrent connections
- **CPU-bound:** More workers help parallelize CPU-intensive tasks
- **Start with:** 2-4 workers and monitor performance

## Common Issues

### ASGI Application Not Found

**Symptom:** `Error loading ASGI app. Import string "myproject.asgi:application" doesn't exist`

**Solution:**
- Verify your `asgi.py` file exists and defines `application`
- Check your Django project structure
- Ensure ASGI is properly configured in Django settings

### No Async Support

**Symptom:** Async views don't work or raise errors

**Solution:** Use ASGI mode, not WSGI mode:
```python
"BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",  # ASGI
```

Not:
```python
"BACKEND": "django_prodserver.backends.uvicorn.UvicornWSGIServer",  # WSGI
```

### Poor WebSocket Performance

**Symptom:** WebSocket connections timing out or performing poorly

**Solution:** Increase keep-alive timeout:
```python
"ARGS": {
    "timeout-keep-alive": "120",
}
```

### Workers Not Starting

**Symptom:** Workers fail to start with multiple workers

**Solution:** Ensure you're not using reload mode with multiple workers:
```python
"ARGS": {
    "workers": "4",
    # Remove "reload": "True"
}
```

## Performance Tuning

### Event Loop Selection

For best performance, use uvloop:

```bash
pip install uvicorn[standard]
```

```python
"ARGS": {
    "loop": "uvloop",
}
```

### Disable Access Logs

In high-traffic scenarios:

```python
"ARGS": {
    "no-access-log": "True",
}
```

Use your reverse proxy (nginx) for access logging instead.

### Connection Limits

Prevent resource exhaustion:

```python
"ARGS": {
    "limit-concurrency": "1000",
    "limit-max-requests": "10000",
}
```

### Backlog Tuning

For high connection rates:

```python
"ARGS": {
    "backlog": "4096",
}
```

## Integration Examples

### With Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "manage.py", "prodserver", "web"]
```

```python
# settings.py
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

### With systemd

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=MyApp Uvicorn Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/myapp
Environment="PATH=/var/www/myapp/venv/bin"
ExecStart=/var/www/myapp/venv/bin/python manage.py prodserver web
Restart=always

[Install]
WantedBy=multi-user.target
```

### With nginx

```nginx
# /etc/nginx/sites-available/myapp
upstream myapp {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://myapp;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://myapp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Migration from Other Servers

### From Gunicorn

1. Change backend:
```python
# Before
"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",

# After (for async apps)
"BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
```

2. Update ARGS:
```python
# Before (Gunicorn)
"ARGS": {
    "bind": "0.0.0.0:8000",
    "workers": "4",
}

# After (Uvicorn)
"ARGS": {
    "host": "0.0.0.0",
    "port": "8000",
    "workers": "4",
}
```

See {ref}`guide-backend-switching` for detailed migration guides.

## Official Documentation

For complete Uvicorn documentation:
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Deployment Guide](https://www.uvicorn.org/deployment/)
- [Settings Reference](https://www.uvicorn.org/settings/)
- [Server Behavior](https://www.uvicorn.org/server-behavior/)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-docker` - Docker deployment guide
- {ref}`guide-backend-switching` - Migrating between backends
- {ref}`backend-granian-asgi` - Alternative high-performance ASGI server
- {ref}`backend-gunicorn` - Traditional WSGI alternative
- {ref}`troubleshooting` - General troubleshooting guide
