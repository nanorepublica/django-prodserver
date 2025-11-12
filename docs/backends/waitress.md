(backend-waitress)=

# Waitress

Waitress is a production-quality pure Python WSGI server with excellent Windows support. It's simple to configure, requires no platform-specific dependencies, and is ideal for environments where compilation is problematic.

## Overview

Waitress is a pure Python HTTP server that serves WSGI applications. Unlike Gunicorn (Linux-only) or Uvicorn (requires compilation), Waitress works identically across all platforms and requires no C extensions.

## When to Use

**Choose Waitress when you need:**
- Windows production deployments
- Pure Python environment (no C extensions)
- Simple, no-configuration server setup
- Cross-platform consistency
- Deployment without compilation requirements

**Consider alternatives if:**
- You're on Linux and need maximum performance → Use {ref}`backend-gunicorn` or {ref}`backend-granian-wsgi`
- You need async/await support → Use {ref}`backend-uvicorn-asgi`
- You need WebSocket support → Use {ref}`backend-uvicorn-asgi`

## Installation

Install Waitress via pip:

```bash
pip install waitress
```

No additional dependencies or compilation required!

For more installation options, see the [official Waitress documentation](https://docs.pylonsproject.org/projects/waitress/).

## Basic Configuration

### Minimal Setup

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "port": "8000",
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
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "threads": "4",
            "channel-timeout": "60",
        }
    }
}
```

## ARGS Translation

The `ARGS` dictionary is translated to Waitress command-line arguments:

```python
"ARGS": {
    "host": "0.0.0.0",           # --host=0.0.0.0
    "port": "8000",               # --port=8000
    "threads": "4",               # --threads=4
    "channel-timeout": "60",      # --channel-timeout=60
}
```

This translates to:
```bash
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 --channel-timeout=60 myproject.wsgi:application
```

## Configuration Reference

### Common ARGS Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `host` | string | `0.0.0.0` | The host to bind (use `127.0.0.1` for localhost only) |
| `port` | integer | `8080` | The port to bind |
| `threads` | integer | `4` | Number of threads for handling requests |
| `channel-timeout` | integer | `120` | Channel timeout in seconds |
| `connection-limit` | integer | `100` | Maximum number of simultaneous connections |
| `recv-bytes` | integer | `8192` | Number of bytes to request when calling socket.recv() |
| `send-bytes` | integer | `18000` | Number of bytes to send when calling socket.send() |
| `url-scheme` | string | `http` | URL scheme (`http` or `https`) |

### Advanced Options

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `listen` | string | None | Alternative socket binding (e.g., `"localhost:8080"`) |
| `unix-socket` | string | None | Unix socket path (not supported on Windows) |
| `unix-socket-perms` | string | `600` | Unix socket permissions |
| `backlog` | integer | `1024` | Socket backlog size |
| `ident` | string | `waitress` | Server identifier in responses |
| `expose-tracebacks` | boolean | `False` | Expose tracebacks in 500 errors (development only) |
| `asyncore-loop-timeout` | integer | `1` | Asyncore loop timeout |
| `asyncore-use-poll` | boolean | Platform-dependent | Use poll() instead of select() |

For complete options, see the [Waitress documentation](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html).

## Advanced Examples

### High-Concurrency Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "threads": "8",
            "connection-limit": "500",
            "channel-timeout": "120",
            "backlog": "2048",
        }
    }
}
```

**Configuration explanation:**
- `threads: 8` - More threads for concurrent requests
- `connection-limit: 500` - Allow more simultaneous connections
- `channel-timeout: 120` - Longer timeout for slow operations
- `backlog: 2048` - Larger connection queue

### Windows Production Server

```python
# settings_windows.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "80",  # Standard HTTP port (requires admin on Windows)
            "threads": "6",
            "channel-timeout": "90",
            "url-scheme": "http",
        }
    }
}
```

### Behind a Reverse Proxy

For use with nginx, IIS, or another reverse proxy:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "threads": "4",
            "url-scheme": "http",
        }
    }
}
```

### Development with Error Tracebacks

```python
# settings_dev.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "threads": "2",
            "expose-tracebacks": "True",
        }
    }
}
```

::::{warning}
Never use `expose-tracebacks: True` in production - it exposes sensitive information in error pages.
::::

### Unix Socket (Linux/macOS)

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "unix-socket": "/var/run/myapp.sock",
            "unix-socket-perms": "660",
            "threads": "4",
        }
    }
}
```

## Thread Count Recommendations

Waitress uses a thread pool model. Thread recommendations:

**Formula:** `4-8 threads as a starting point`

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "threads": "6",
        }
    }
}
```

**Guidelines:**
- **Low traffic:** 2-4 threads
- **Medium traffic:** 4-8 threads
- **High traffic:** 8-16 threads
- **Monitor:** Watch CPU and memory usage to optimize
- **Don't overdo it:** More threads isn't always better

## Common Issues

### Port Already in Use

**Symptom:** `socket.error: [Errno 48] Address already in use`

**Solution:**
- Stop any process using that port
- Change the port number:
```python
"ARGS": {
    "port": "8001",  # Use different port
}
```

### Permission Denied on Port 80 (Windows)

**Symptom:** Cannot bind to port 80 on Windows

**Solution:**
- Run as Administrator
- Or use a higher port (8000, 8080) and reverse proxy

### Slow Response Times

**Symptom:** Requests are slow or timing out

**Solution:** Increase thread count and timeout:
```python
"ARGS": {
    "threads": "8",
    "channel-timeout": "120",
}
```

### Too Many Connections Rejected

**Symptom:** `ConnectionRefusedError` under high load

**Solution:** Increase connection limit and backlog:
```python
"ARGS": {
    "connection-limit": "500",
    "backlog": "2048",
}
```

## Performance Tuning

### Optimize for Throughput

```python
"ARGS": {
    "threads": "8",
    "connection-limit": "500",
    "backlog": "2048",
    "recv-bytes": "16384",
    "send-bytes": "32000",
}
```

### Optimize for Low Latency

```python
"ARGS": {
    "threads": "4",
    "connection-limit": "100",
    "channel-timeout": "30",
}
```

### Balance Resources

```python
"ARGS": {
    "threads": "6",
    "connection-limit": "200",
    "channel-timeout": "60",
    "backlog": "1024",
}
```

## Integration Examples

### With Windows Service

```python
# service.py using pywin32
import servicemanager
import win32serviceutil
import subprocess

class MyAppService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyAppService"
    _svc_display_name_ = "MyApp Django Service"

    def SvcDoRun(self):
        subprocess.call(['python', 'manage.py', 'prodserver', 'web'])
```

### With Docker (Windows Containers)

```dockerfile
# Dockerfile (Windows)
FROM mcr.microsoft.com/windows/servercore:ltsc2022
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "manage.py", "prodserver", "web"]
```

### With IIS as Reverse Proxy

```xml
<!-- web.config -->
<configuration>
  <system.webServer>
    <httpPlatform processPath="C:\path\to\python.exe"
                  arguments="C:\path\to\manage.py prodserver web"
                  stdoutLogEnabled="true"
                  startupTimeLimit="60">
    </httpPlatform>
  </system.webServer>
</configuration>
```

### With systemd (Linux)

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=MyApp Waitress Server
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

## Windows vs Linux Considerations

### Windows Specific

**Advantages:**
- Native Windows support (unlike Gunicorn)
- Works with Windows Services
- Compatible with IIS reverse proxy
- No compilation required

**Considerations:**
- Use higher ports (8000+) unless running as Administrator
- Windows Services for background operation
- IIS or nginx for reverse proxy

### Linux Specific

**Advantages:**
- Works identically to Windows
- Unix socket support
- systemd integration
- nginx reverse proxy

**Considerations:**
- Gunicorn may perform better on Linux
- But Waitress offers cross-platform consistency

## Migration from Other Servers

### From Gunicorn (to Windows)

```python
# Before (Gunicorn - Linux only)
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
        }
    }
}

# After (Waitress - Windows compatible)
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

See {ref}`guide-backend-switching` for detailed migration guides.

## Official Documentation

For complete Waitress documentation:
- [Waitress Documentation](https://docs.pylonsproject.org/projects/waitress/)
- [Arguments Reference](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html)
- [Runner Script](https://docs.pylonsproject.org/projects/waitress/en/stable/runner.html)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-docker` - Docker deployment guide
- {ref}`guide-backend-switching` - Migrating between backends
- {ref}`backend-gunicorn` - Linux alternative
- {ref}`troubleshooting` - General troubleshooting guide
