(backend-gunicorn)=

# Gunicorn

Gunicorn (Green Unicorn) is a mature, battle-tested Python WSGI HTTP server for Unix systems. It's the industry standard for serving Django applications in production.

## Overview

Gunicorn is a pre-fork worker model server. It forks multiple worker processes to handle requests, providing better concurrency and stability compared to single-threaded servers. It's simple to configure, widely deployed, and well-documented.

## When to Use

**Choose Gunicorn when you need:**
- Production-ready WSGI server for traditional Django applications
- Battle-tested reliability and stability
- Simple configuration and deployment
- Linux/Unix production environments
- Industry-standard deployment practices

**Don't use Gunicorn if:**
- You need async/await support (use {ref}`backend-uvicorn-asgi` instead)
- You're deploying on Windows (use {ref}`backend-waitress` instead)
- You need WebSocket support (use {ref}`backend-uvicorn-asgi` instead)

## Installation

Install Gunicorn via pip:

```bash
pip install gunicorn
```

For more installation options, see the [official Gunicorn documentation](https://docs.gunicorn.org/en/stable/install.html).

## Basic Configuration

### Minimal Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
        }
    }
}
```

Start the server:
```bash
python manage.py prodserver web
```

### Recommended Production Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "timeout": "60",
            "worker-class": "sync",
        }
    }
}
```

## ARGS Translation

The `ARGS` dictionary is translated to Gunicorn command-line arguments:

```python
"ARGS": {
    "bind": "0.0.0.0:8000",      # --bind=0.0.0.0:8000
    "workers": "4",               # --workers=4
    "timeout": "60",              # --timeout=60
    "worker-class": "sync",       # --worker-class=sync
}
```

This translates to:
```bash
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=60 --worker-class=sync myproject.wsgi:application
```

## Configuration Reference

### Common ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `bind` | string | `127.0.0.1:8000` | The socket to bind (host:port or unix socket path) |
| `workers` | integer | `1` | Number of worker processes (recommended: `2-4 x CPU_cores`) |
| `worker-class` | string | `sync` | Type of workers (`sync`, `gevent`, `eventlet`, `tornado`) |
| `timeout` | integer | `30` | Workers silent for more than this many seconds are killed |
| `keepalive` | integer | `2` | Seconds to wait for requests on Keep-Alive connections |
| `max-requests` | integer | `0` | Maximum number of requests a worker will process before restarting |
| `max-requests-jitter` | integer | `0` | Random jitter to add to max-requests |
| `threads` | integer | `1` | Number of threads per worker (for threaded workers) |
| `worker-connections` | integer | `1000` | Maximum number of simultaneous clients (for async workers) |

### Logging Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `accesslog` | string | `None` | Access log file path (`-` for stdout) |
| `errorlog` | string | `stderr` | Error log file path |
| `loglevel` | string | `info` | Log level (`debug`, `info`, `warning`, `error`, `critical`) |
| `access-logformat` | string | | Custom access log format |
| `capture-output` | boolean | `False` | Redirect stdout/stderr to error log |

### Process Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `daemon` | boolean | `False` | Daemonize the Gunicorn process |
| `pidfile` | string | `None` | Path to PID file |
| `user` | string/int | Current user | User to run workers as |
| `group` | string/int | Current group | Group to run workers as |
| `umask` | integer | `0` | Umask to use when creating files |
| `reload` | boolean | `False` | Restart workers when code changes (development only) |

For complete options, see the [Gunicorn Settings Documentation](https://docs.gunicorn.org/en/stable/settings.html).

## Advanced Examples

### High-Traffic Production Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "8",
            "worker-class": "gevent",
            "worker-connections": "1000",
            "timeout": "120",
            "max-requests": "1000",
            "max-requests-jitter": "100",
            "keepalive": "5",
            "accesslog": "/var/log/myapp/gunicorn-access.log",
            "errorlog": "/var/log/myapp/gunicorn-error.log",
            "loglevel": "info",
        }
    }
}
```

**Configuration explanation:**
- `workers: 8` - Handles concurrent requests across 8 processes
- `worker-class: gevent` - Uses gevent for better I/O concurrency
- `max-requests: 1000` - Restart workers after 1000 requests (prevents memory leaks)
- `max-requests-jitter: 100` - Adds randomness to prevent all workers restarting simultaneously

### Gevent Async Workers

For applications with many I/O-bound operations:

```python
# First install: pip install gunicorn[gevent]

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "worker-class": "gevent",
            "worker-connections": "1000",
            "timeout": "90",
        }
    }
}
```

### Unix Socket Binding

For use behind nginx or another reverse proxy:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "unix:/var/run/myapp.sock",
            "workers": "4",
            "timeout": "60",
            "user": "www-data",
            "group": "www-data",
        }
    }
}
```

### Development Configuration with Auto-Reload

For development environments (not recommended for production):

```python
# settings_dev.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "127.0.0.1:8000",
            "workers": "1",
            "reload": "True",
            "loglevel": "debug",
            "accesslog": "-",  # Log to stdout
        }
    }
}
```

::::{warning}
Never use `reload: True` in production - it watches file changes and restarts workers, which impacts performance and stability.
::::

## Worker Count Recommendations

The optimal number of workers depends on your application:

**Formula:** `(2 x CPU_cores) + 1`

```python
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": str(workers),
        }
    }
}
```

**Guidelines:**
- **CPU-bound apps:** Fewer workers (1-2 per core)
- **I/O-bound apps:** More workers (2-4 per core) or use gevent
- **Start conservative:** Begin with 2-4 workers and monitor resource usage
- **Monitor and adjust:** Use metrics to find the right balance

## Common Issues

### Worker Timeout Errors

**Symptom:** Workers are being killed with timeout errors

**Solution:** Increase the timeout value:
```python
"ARGS": {
    "timeout": "120",  # Increase from default 30s
}
```

Or investigate slow requests that exceed the timeout.

### Too Many Workers

**Symptom:** High memory usage, system slowdown

**Solution:** Reduce worker count:
```python
"ARGS": {
    "workers": "4",  # Reduce number of workers
}
```

Monitor memory usage and find the optimal balance.

### Port Already in Use

**Symptom:** `[ERROR] Connection in use: ('0.0.0.0', 8000)`

**Solution:**
- Stop any process using that port
- Change the port number:
```python
"ARGS": {
    "bind": "0.0.0.0:8001",  # Use different port
}
```

### Worker Class Not Found

**Symptom:** `ImportError: No module named 'gevent'`

**Solution:** Install the required worker class:
```bash
pip install gunicorn[gevent]  # For gevent workers
pip install gunicorn[eventlet]  # For eventlet workers
```

## Performance Tuning

### Graceful Worker Restarts

Prevent memory leaks by periodically restarting workers:

```python
"ARGS": {
    "max-requests": "1000",
    "max-requests-jitter": "100",
}
```

### Connection Keep-Alive

Reduce connection overhead for clients making multiple requests:

```python
"ARGS": {
    "keepalive": "5",  # Keep connections alive for 5 seconds
}
```

### Access Log Optimization

Disable access logs in high-traffic scenarios to reduce I/O:

```python
"ARGS": {
    "accesslog": None,  # Disable access logging
    "errorlog": "/var/log/myapp/error.log",
}
```

Or use log buffering in your reverse proxy (nginx, etc.) instead.

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
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
        }
    }
}
```

See {ref}`guide-docker` for complete Docker deployment examples.

### With systemd

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=MyApp Gunicorn Server
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

See {ref}`guide-multi-process` for more systemd examples.

## Official Documentation

For complete Gunicorn documentation:
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Configuration Guide](https://docs.gunicorn.org/en/stable/settings.html)
- [Deployment Guide](https://docs.gunicorn.org/en/stable/deploy.html)
- [Design Overview](https://docs.gunicorn.org/en/stable/design.html)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-docker` - Docker deployment guide
- {ref}`guide-multi-process` - Multi-process deployments
- {ref}`guide-backend-switching` - Migrating to/from other backends
- {ref}`troubleshooting` - General troubleshooting guide
