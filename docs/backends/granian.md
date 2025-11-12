(backend-granian)=

# Granian

Granian is a modern, high-performance HTTP server built with Rust. It supports both ASGI and WSGI interfaces, delivering excellent performance for both async and traditional Django applications.

## Overview

Granian is powered by Rust's hyper HTTP library and provides two modes:

- **Granian ASGI** - For async Django apps with WebSocket support
- **Granian WSGI** - For traditional Django apps with high performance

Both modes share Granian's core performance characteristics and are configured similarly.

(backend-granian-asgi)=

## Granian ASGI Mode

Use ASGI mode for async Django applications with WebSocket and async view support.

### When to Use

**Choose Granian ASGI when you need:**
- Maximum performance for async applications
- Rust-powered server with minimal overhead
- WebSocket support
- Modern async/await Django features
- Better resource utilization than Python-based servers

**Consider alternatives if:**
- You don't need async features → Use {ref}`backend-granian-wsgi`
- You want more mature ecosystem → Use {ref}`backend-uvicorn-asgi`
- Your team prefers pure Python → Use {ref}`backend-uvicorn-asgi`

### Installation

Install Granian via pip:

```bash
pip install granian
```

For more installation options, see the [official Granian documentation](https://github.com/emmett-framework/granian).

### Basic Configuration

#### Minimal Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
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
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "threads": "1",
            "log-level": "info",
        }
    }
}
```

### ARGS Translation for ASGI

Granian uses a different configuration pattern - ARGS are passed as constructor parameters:

```python
"ARGS": {
    "address": "0.0.0.0",
    "port": "8000",
    "workers": "4",
    "blocking-threads": "1",
}
```

This creates a Granian instance with these parameters.

(backend-granian-wsgi)=

## Granian WSGI Mode

Use WSGI mode for traditional Django applications with Rust-powered performance.

### When to Use

**Choose Granian WSGI when you need:**
- High performance for traditional Django apps
- Rust-powered server benefits without async complexity
- Better performance than Gunicorn
- Modern server with traditional WSGI interface

**Consider alternatives if:**
- You need async features → Use {ref}`backend-granian-asgi`
- You want industry standard → Use {ref}`backend-gunicorn`
- You need Windows support → Use {ref}`backend-waitress`

### Basic Configuration

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "threads": "2",
        }
    }
}
```

## Configuration Reference

### Common ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `address` / `host` | string | `127.0.0.1` | The address to bind |
| `port` | integer | `8000` | The port to bind |
| `workers` | integer | `1` | Number of worker processes |
| `threads` / `blocking-threads` | integer | `1` | Number of blocking threads per worker |
| `runtime-threads` | integer | CPU count | Number of runtime threads for async operations |
| `backlog` | integer | `1024` | Maximum number of pending connections |
| `http` | string | `auto` | HTTP version (`auto`, `1`, `2`) |

### Logging Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `log-level` | string | `info` | Log level (`critical`, `error`, `warn`, `info`, `debug`) |
| `log-access` | boolean | `True` | Enable access logging |

### Advanced Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `websockets` | boolean | `True` | Enable WebSocket support (ASGI only) |
| `ssl-cert` | string | `None` | Path to SSL certificate file |
| `ssl-key` | string | `None` | Path to SSL key file |
| `url-path-prefix` | string | `None` | URL path prefix for routing |
| `reload` | boolean | `False` | Enable auto-reload (development only) |

For complete options, see the [Granian documentation](https://github.com/emmett-framework/granian).

## Advanced Examples

### High-Performance ASGI Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "blocking-threads": "2",
            "runtime-threads": "8",
            "backlog": "2048",
            "log-level": "warn",
            "log-access": "False",
        }
    }
}
```

**Configuration explanation:**
- `workers: 4` - Multiple processes for concurrency
- `blocking-threads: 2` - Threads for blocking operations
- `runtime-threads: 8` - Threads for async runtime
- `log-access: False` - Disable access logs for performance

### WSGI with Thread Pool

For I/O-bound traditional Django apps:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianWSGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "workers": "2",
            "threads": "4",  # More threads per worker
            "log-level": "info",
        }
    }
}
```

### With SSL/TLS

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "443",
            "ssl-cert": "/path/to/cert.pem",
            "ssl-key": "/path/to/key.pem",
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
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "127.0.0.1",
            "port": "8000",
            "reload": "True",
            "log-level": "debug",
        }
    }
}
```

::::{warning}
Never use `reload: True` in production - it impacts performance and stability.
::::

### HTTP/2 Support

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
            "port": "8000",
            "http": "2",
            "workers": "4",
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
| **Performance** | Excellent | Excellent |
| **Thread Model** | Async + Blocking threads | Thread pool |

**When to use each:**
- **ASGI Mode:** Your app uses async views, WebSockets, or async ORM queries
- **WSGI Mode:** Traditional Django app with Rust performance benefits

## Worker and Thread Recommendations

Granian's architecture is different from traditional servers:

**Workers:** Process-based parallelism
```python
import multiprocessing
workers = multiprocessing.cpu_count()
```

**Blocking Threads (ASGI):** For blocking I/O in async apps
```python
"blocking-threads": "2"  # 1-2 per worker
```

**Threads (WSGI):** Thread pool for traditional apps
```python
"threads": "4"  # 2-4 per worker for I/O-bound apps
```

**Runtime Threads (ASGI):** Async runtime threads
```python
"runtime-threads": str(multiprocessing.cpu_count())
```

**Guidelines:**
- **CPU-bound:** More workers, fewer threads
- **I/O-bound WSGI:** Fewer workers, more threads
- **I/O-bound ASGI:** Moderate workers, adjust blocking threads
- **Start with:** 2-4 workers and monitor

## Common Issues

### Installation Errors on Some Platforms

**Symptom:** Granian fails to install on your platform

**Solution:**
- Granian requires a Rust compiler for some platforms
- Try using pre-built wheels: `pip install --upgrade granian`
- Check [platform compatibility](https://github.com/emmett-framework/granian#installation)

### ASGI Application Not Found

**Symptom:** Error loading ASGI application

**Solution:**
- Verify your `asgi.py` file exists and defines `application`
- Ensure ASGI is properly configured in Django settings
- Use ASGI backend, not WSGI backend

### WebSocket Connection Issues

**Symptom:** WebSocket connections fail or disconnect

**Solution:** Ensure WebSocket support is enabled (ASGI mode):
```python
"ARGS": {
    "websockets": "True",
}
```

### Performance Not as Expected

**Symptom:** Performance similar to other servers

**Solution:** Tune workers and threads:
```python
"ARGS": {
    "workers": "4",
    "blocking-threads": "2",  # ASGI
    "threads": "4",            # WSGI
    "runtime-threads": "8",    # ASGI
}
```

## Performance Tuning

### Maximize Throughput

```python
"ARGS": {
    "workers": "8",
    "backlog": "4096",
    "log-access": "False",
    "log-level": "warn",
}
```

### Optimize for Low Latency

```python
"ARGS": {
    "workers": "2",
    "blocking-threads": "1",
    "runtime-threads": "4",
}
```

### Balance Resources

```python
"ARGS": {
    "workers": "4",
    "threads": "2",
    "backlog": "2048",
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
        "BACKEND": "django_prodserver.backends.granian.GranianASGIServer",
        "ARGS": {
            "address": "0.0.0.0",
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
Description=MyApp Granian Server
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

## Migration from Other Servers

### From Uvicorn

```python
# Before (Uvicorn)
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

# After (Granian ASGI)
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

### From Gunicorn

```python
# Before (Gunicorn)
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
        }
    }
}

# After (Granian WSGI)
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

See {ref}`guide-backend-switching` for detailed migration guides.

## Official Documentation

For complete Granian documentation:
- [Granian GitHub Repository](https://github.com/emmett-framework/granian)
- [Granian Documentation](https://github.com/emmett-framework/granian#documentation)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-docker` - Docker deployment guide
- {ref}`guide-backend-switching` - Migrating between backends
- {ref}`backend-uvicorn-asgi` - Alternative ASGI server
- {ref}`backend-gunicorn` - WSGI alternative
- {ref}`troubleshooting` - General troubleshooting guide
