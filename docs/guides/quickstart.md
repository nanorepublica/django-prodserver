(guide-quickstart)=

# Quickstart Guide

Get django-prodserver up and running in 10 minutes or less! This tutorial walks you through installation, configuration, and running your first production server.

## What You'll Accomplish

By the end of this guide, you'll have:
- django-prodserver installed in your Django project
- A production-ready web server (Gunicorn) configured
- Your Django application running in production mode
- Understanding of how to deploy to production

## Prerequisites

- Python 3.8 or higher
- An existing Django project (Django 3.2+)
- Basic familiarity with Django and command line

## Step 1: Install django-prodserver

Install the package using pip:

```bash
pip install django-prodserver
```

::::{tip}
For production use, you'll also need a server backend. We'll use Gunicorn for this quickstart:
```bash
pip install gunicorn
```
::::

## Step 2: Add to INSTALLED_APPS

Open your `settings.py` and add `django_prodserver` to `INSTALLED_APPS`:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your apps
    # ...

    # Add django-prodserver
    'django_prodserver',
]
```

::::{note}
No migrations are needed - django-prodserver doesn't add any database tables.
::::

## Step 3: Configure Your Production Server

Add the `PRODUCTION_PROCESSES` configuration to your `settings.py`:

```python
# settings.py

# Production server configuration
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "2",
        }
    }
}
```

**What this configuration does:**
- Creates a process named "web"
- Uses Gunicorn as the server backend
- Binds to all interfaces (0.0.0.0) on port 8000
- Runs with 2 worker processes for handling concurrent requests

## Step 4: Run Your Production Server

Start your server with the `prodserver` management command:

```bash
python manage.py prodserver web
```

You should see output like:

```
[2025-01-12 10:30:00 +0000] [12345] [INFO] Starting gunicorn 21.2.0
[2025-01-12 10:30:00 +0000] [12345] [INFO] Listening at: http://0.0.0.0:8000 (12345)
[2025-01-12 10:30:00 +0000] [12345] [INFO] Using worker: sync
[2025-01-12 10:30:00 +0000] [12347] [INFO] Booting worker with pid: 12347
[2025-01-12 10:30:00 +0000] [12348] [INFO] Booting worker with pid: 12348
```

## Step 5: Test Your Application

Open your browser and visit:

```
http://localhost:8000
```

You should see your Django application running! Try navigating to different pages to verify everything works.

::::{important}
**You're now running a production-ready server!** This is much more robust than Django's development server (`runserver`).
::::

## Congratulations!

You've successfully set up django-prodserver! Your Django application is now running with:

- **Gunicorn**: Industry-standard WSGI server
- **Multiple workers**: Handling concurrent requests
- **Production-ready**: Suitable for real deployments

## Next Steps

### Add Background Workers

Process tasks asynchronously with Celery:

```python
# settings.py
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "2",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "2",
        }
    }
}
```

See {ref}`backend-celery-worker` for Celery setup.

### Deploy with Docker

Containerize your application:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "prodserver", "web"]
```

See {ref}`guide-docker` for complete Docker deployment.

### Configure for Different Environments

Set up development, staging, and production configurations:

```python
# settings_prod.py
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['example.com']

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

See {ref}`guide-environment-configs` for environment-specific configurations.

### Try Different Backends

Explore other server backends:

- **{ref}`backend-uvicorn-asgi`** - For async Django applications
- **{ref}`backend-granian-asgi`** - High-performance Rust-based server
- **{ref}`backend-waitress`** - For Windows deployments
- **{ref}`backend-django-tasks`** - Lightweight background tasks

### Learn More

- {ref}`usage` - Detailed usage patterns and examples
- {ref}`configuration-reference` - Complete configuration reference
- {ref}`backend-reference` - All available backends
- {ref}`guide-multi-process` - Running multiple processes
- {ref}`troubleshooting` - Common issues and solutions

## Common Questions

**Q: How is this different from `python manage.py runserver`?**

A: Django's `runserver` is for development only. django-prodserver uses production-ready servers like Gunicorn that are:
- Much faster (multiple workers)
- More stable (automatic worker restarts)
- More secure (designed for production)
- Better at handling concurrent requests

**Q: Can I use this in development?**

A: Yes, but `runserver` is better for development because it auto-reloads when code changes. Use `prodserver` for staging, testing production configurations, and production deployments.

**Q: Do I need to configure nginx or Apache?**

A: Not necessarily! Gunicorn can serve your application directly. However, for production, it's recommended to use a reverse proxy (nginx/Apache) for:
- SSL/TLS termination
- Static file serving
- Load balancing
- Additional security features

**Q: How many workers should I use?**

A: A good starting point is `(2 × CPU_cores) + 1`. For example, on a 2-core machine:
```python
"workers": "5"  # (2 × 2) + 1
```
Monitor your application and adjust based on resource usage.

**Q: What if I get errors?**

A: Check the {ref}`troubleshooting` guide for common issues. Common problems:
- Backend not installed: `pip install gunicorn`
- Port in use: Change the port number
- Settings not found: Ensure `PRODUCTION_PROCESSES` is in your settings

## Quick Reference

### Basic Commands

```bash
# Start web server
python manage.py prodserver web

# Start with specific settings
python manage.py prodserver web --settings=myproject.settings_prod

# Run in foreground (Ctrl+C to stop)
python manage.py prodserver web
```

### Basic Configuration

```python
# Minimal
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"}
    }
}

# Recommended
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

## Troubleshooting

**Server won't start:**
```bash
# Check if gunicorn is installed
pip install gunicorn

# Verify settings are correct
python manage.py check

# Check if port is already in use
# On Linux/macOS:
lsof -i :8000
# On Windows:
netstat -ano | findstr :8000
```

**ImportError: No module named 'gunicorn':**
```bash
pip install gunicorn
```

**Port already in use:**
```python
# Change port in settings.py
"ARGS": {
    "bind": "0.0.0.0:8001",  # Use different port
}
```

For more help, see {ref}`troubleshooting`.

## Summary

You've learned how to:
1. Install django-prodserver and a backend (Gunicorn)
2. Add django-prodserver to your Django project
3. Configure a production server
4. Run your application in production mode
5. Understand next steps for advanced deployments

**Ready for production?** You're all set to deploy! Check out the {ref}`practical-guides` for Docker, environment configs, and multi-process deployments.
