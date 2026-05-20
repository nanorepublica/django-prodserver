(usage)=

# Usage

## Basic Commands

Start a web/ASGI/WSGI process with the `server` command:

```bash
python manage.py server <process_name>
```

Start a background task worker with the `worker` command:

```bash
python manage.py worker <process_name>
```

Both commands read from the same `PRODUCTION_PROCESSES` setting. `server` only
accepts server backends and `worker` only accepts worker backends; pointing one
at the wrong kind of backend produces an error telling you which command to use.
Pass `--list` to either command to print the configured process names.

### System checks

Before starting a process, `server` and `worker` run Django's system checks.
Pass `--skip-checks` to bypass them:

```bash
python manage.py server web --skip-checks
```

### Forwarding arguments to the backend

Arguments that the command does not recognise are forwarded to the underlying
process (gunicorn, uvicorn, waitress, celery, ...) and appended after the
`ARGS` configured in `PRODUCTION_PROCESSES`:

```bash
python manage.py server web --timeout=120
```

Backends that build their server programmatically rather than from a
command line — Granian and the `devserver`-style runserver backends — cannot
accept forwarded arguments and will raise an error if any are passed.

```{deprecated} 3.0.0
The `prodserver` command has been renamed to `server`. The old name continues
to work as an alias but will be removed in django-prodserver 4.0.0.
```

## Common Patterns

### Single Web Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    }
}
```

```bash
python manage.py server web
```

### Web + Worker

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
}
```

```bash
# Run in separate terminals/services
python manage.py server web
python manage.py worker worker
```

### Full Stack (Web + Worker + Scheduler)

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.uvicorn.UvicornServer",
        "ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.workers.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {"loglevel": "info"},
    },
}
```

---

(process-management)=

## Process Management

### Understanding Process Names

Process names in `PRODUCTION_PROCESSES` are arbitrary - you can use any name that makes sense for your application:

```python
PRODUCTION_PROCESSES = {
    "web": {...},           # Common convention for web servers
    "api": {...},           # Could be a separate API server
    "worker": {...},        # Background task worker
    "beat": {...},          # Scheduled task runner
    "priority_worker": {...},  # High-priority task worker
    "email_worker": {...},  # Dedicated email worker
}
```

### Process Supervision

**systemd:**

```ini
# /etc/systemd/system/myapp-web.service
[Unit]
Description=MyApp Web Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/myproject
ExecStart=/path/to/venv/bin/python manage.py server web
Restart=always

[Install]
WantedBy=multi-user.target
```

**Docker Compose:**

```yaml
services:
  web:
    command: python manage.py server web
  worker:
    command: python manage.py worker worker
```

See {ref}`guide-multi-process` for complete examples.

---

(development-vs-production)=

## Development vs Production

| Command                       | Use Case                               |
| ----------------------------- | -------------------------------------- |
| `python manage.py devserver`  | Local development (auto-reload, debug) |
| `python manage.py server web` | Production (multi-worker, optimized)   |

### Environment-Specific Settings

```python
# settings_prod.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.servers.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4", "timeout": "60"},
    },
}
```

```bash
python manage.py server web --settings=myproject.settings_prod
```

---

## Advanced Usage

### Custom Backends

Subclass `BaseServerBackend` for a web server, or `BaseWorkerBackend` for a
background task worker:

```python
from django_prodserver.backends.base import BaseServerBackend

class CustomServer(BaseServerBackend):
    def start_server(self, *args: str) -> None:
        # Custom startup logic
        pass
```

```python
from django_prodserver.backends.base import BaseWorkerBackend

class CustomWorker(BaseWorkerBackend):
    def start_server(self, *args: str) -> None:
        # Custom worker startup logic
        pass
```

```python
PRODUCTION_PROCESSES = {
    "custom": {
        "BACKEND": "myproject.backends.CustomServer",
        "ARGS": {...},
    }
}
```

### ARGS Translation

ARGS are converted to CLI arguments:

```python
"ARGS": {
    "bind": "0.0.0.0:8000",  # --bind=0.0.0.0:8000
    "workers": "4",           # --workers=4
}
```

See {ref}`backend-reference` for backend-specific ARGS.

---

## Next Steps

- {ref}`backend-reference` - Backend-specific configuration
- {ref}`configuration-reference` - Full configuration options
- {ref}`practical-guides` - Deployment tutorials
