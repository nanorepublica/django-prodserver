(usage)=

# Usage

Once you've configured your `PRODUCTION_PROCESSES` setting, you can start managing your production servers and workers with simple management commands.

## Basic Usage

Start any configured process by name:

```bash
python manage.py prodserver <process_name>
```

For example, if you have a "web" process configured:

```bash
python manage.py prodserver web
```

Or a "worker" process:

```bash
python manage.py prodserver worker
```

(usage-patterns)=

## Common Usage Patterns

### Single Web Server

The most basic setup - a single web server process:

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

Start the server:
```bash
python manage.py prodserver web
```

### Web Server with Background Worker

A common production setup with web serving and task processing:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
            "loglevel": "info",
        }
    }
}
```

Start each process (typically in separate terminals or services):
```bash
# Terminal 1 - Web server
python manage.py prodserver web

# Terminal 2 - Background worker
python manage.py prodserver worker
```

### Complete Application Stack

Web server + worker + scheduler for a full production deployment:

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
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
        }
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "info",
        }
    }
}
```

Start all processes:
```bash
# Terminal 1
python manage.py prodserver web

# Terminal 2
python manage.py prodserver worker

# Terminal 3
python manage.py prodserver beat
```

See {ref}`guide-multi-process` for managing multiple processes with systemd or Docker.

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

### Running Specific Processes

Always specify which process to run:

```bash
python manage.py prodserver web
python manage.py prodserver worker
python manage.py prodserver beat
```

### Process Supervision

In production, you'll typically use a process supervisor to manage your processes:

**systemd (Linux):**
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

(multiple-processes)=

## Running Multiple Processes

### Separate Process Types

The recommended approach is to run different process types separately:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
}
```

Run them separately:
```bash
# Web process
python manage.py prodserver web

# Worker process (different terminal/service)
python manage.py prodserver worker
```

### Multiple Workers for Different Queues

You can define multiple worker processes for different task queues:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "default_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "queues": "default",
            "concurrency": "4",
        }
    },
    "priority_worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "queues": "priority",
            "concurrency": "2",
        }
    },
}
```

### Scaling by Running Multiple Instances

Run multiple instances of the same process on different ports:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web_8000": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    },
    "web_8001": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8001"},
    },
}
```

Or use a load balancer and multiple worker processes within one server:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "8",  # Multiple worker processes
        }
    },
}
```

(development-vs-production)=

## Development vs Production

### Development Server

For local development, use Django's built-in development server:

```bash
python manage.py runserver
```

The development server provides:
- Auto-reload on code changes
- Detailed error pages
- Static file serving
- **Not suitable for production** (single-threaded, not secure)

### Production Server

For production deployments, use `prodserver`:

```bash
python manage.py prodserver web
```

Production servers provide:
- Multiple worker processes
- Better performance and concurrency
- Production-ready security
- No auto-reload (use process managers for restarts)

### Environment-Specific Configuration

Use different settings files for different environments:

```python
# settings_dev.py
from .settings import *

DEBUG = True
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {"port": "8000"},
    }
}
```

```python
# settings_prod.py
from .settings import *

DEBUG = False
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "timeout": "60",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"},
    },
}
```

Run with different settings:
```bash
# Development
python manage.py runserver --settings=myproject.settings_dev

# Production
python manage.py prodserver web --settings=myproject.settings_prod
```

See {ref}`guide-environment-configs` for more environment configuration patterns.

## Advanced Usage

### Custom Backend Development

You can create custom backends by subclassing `BaseServerBackend`:

```python
# myproject/backends/custom.py
from django_prodserver.backends.base import BaseServerBackend

class CustomServer(BaseServerBackend):
    """Custom server backend."""

    def start_server(self, *args: str) -> None:
        """Start the custom server."""
        # Your custom server startup logic here
        pass
```

Use it in your configuration:

```python
PRODUCTION_PROCESSES = {
    "custom": {
        "BACKEND": "myproject.backends.custom.CustomServer",
        "ARGS": {...},
    }
}
```

For detailed information on creating custom backends, see the source code in `django_prodserver.backends.base.BaseServerBackend`.

### Passing Additional Arguments

The `ARGS` dictionary is converted to command-line arguments:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",      # --bind=0.0.0.0:8000
            "workers": "4",               # --workers=4
            "timeout": "60",              # --timeout=60
            "worker-class": "sync",       # --worker-class=sync
        }
    }
}
```

See individual backend documentation for available arguments:
- {ref}`backend-gunicorn` - Gunicorn arguments
- {ref}`backend-uvicorn-asgi` - Uvicorn arguments
- {ref}`backend-celery-worker` - Celery worker arguments

### Application Path (APP)

Some backends require an `APP` configuration to specify the application path:

```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",  # Path to Celery app instance
        "ARGS": {...},
    }
}
```

This is used for:
- **Celery**: Path to Celery app instance (`myproject.celery.app`)
- Other backends may use it for custom application paths

## Examples and Tutorials

For real-world deployment examples, see:

- {ref}`guide-quickstart` - Get started in 10 minutes
- {ref}`guide-docker` - Docker deployment examples
- {ref}`guide-environment-configs` - Environment-specific configurations
- {ref}`guide-multi-process` - Running multiple process types
- {ref}`guide-backend-switching` - Migrating between backends

## Troubleshooting

Common issues and solutions:

**Process won't start:**
- Check that the backend package is installed (`pip install gunicorn`)
- Verify your `PRODUCTION_PROCESSES` configuration is correct
- Check Django settings are loaded correctly

**Port already in use:**
- Change the port in your `ARGS` configuration
- Stop any other processes using that port

**Backend not found:**
- Verify the `BACKEND` path is correct
- Ensure the backend package is installed

For more detailed troubleshooting, see the {ref}`troubleshooting` guide.

## Next Steps

- Explore {ref}`backend-reference` for detailed backend documentation
- Learn about {ref}`configuration-reference` options
- Check out {ref}`practical-guides` for deployment scenarios
- Review {ref}`troubleshooting` for common issues and solutions
