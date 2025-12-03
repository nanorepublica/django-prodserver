(usage)=

# Usage

## Basic Command

```bash
python manage.py prodserver <process_name>
```

## Common Patterns

### Single Web Server

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    }
}
```

```bash
python manage.py prodserver web
```

### Web + Worker

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
}
```

```bash
# Run in separate terminals/services
python manage.py prodserver web
python manage.py prodserver worker
```

### Full Stack (Web + Worker + Scheduler)

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {"host": "0.0.0.0", "port": "8000", "workers": "4"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
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
ExecStart=/path/to/venv/bin/python manage.py prodserver web
Restart=always

[Install]
WantedBy=multi-user.target
```

**Docker Compose:**

```yaml
services:
  web:
    command: python manage.py prodserver web
  worker:
    command: python manage.py prodserver worker
```

See {ref}`guide-multi-process` for complete examples.

---

(development-vs-production)=

## Development vs Production

| Command                           | Use Case                               |
| --------------------------------- | -------------------------------------- |
| `python manage.py devserver`      | Local development (auto-reload, debug) |
| `python manage.py prodserver web` | Production (multi-worker, optimized)   |

### Environment-Specific Settings

```python
# settings_prod.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000", "workers": "4", "timeout": "60"},
    },
}
```

```bash
python manage.py prodserver web --settings=myproject.settings_prod
```

---

## Advanced Usage

### Custom Backends

```python
from django_prodserver.backends.base import BaseServerBackend

class CustomServer(BaseServerBackend):
    def start_server(self, *args: str) -> None:
        # Custom startup logic
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
