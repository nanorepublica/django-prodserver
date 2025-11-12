(installation)=

# Installation

(quickstart)=

## Quickstart Tutorial

Get django-prodserver up and running in under 10 minutes! This tutorial will guide you through installation, configuration, and running your first production server.

### Step 1: Install the Package

Install django-prodserver using pip (or your preferred package manager):

```bash
pip install django-prodserver
```

::::{tip}
For production use, you'll also need to install your chosen backend. For this quickstart, we'll use Gunicorn:
```bash
pip install gunicorn
```
::::

### Step 2: Add to INSTALLED_APPS

Add `django_prodserver` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    "django_prodserver",
]
```

### Step 3: Configure Your First Server

Add the `PRODUCTION_PROCESSES` configuration to your `settings.py`:

```python
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

This configuration creates a process named "web" that runs Gunicorn with 2 worker processes on port 8000.

### Step 4: Run Your Server

Start your production server with:

```bash
python manage.py prodserver web
```

Visit `http://localhost:8000` and you should see your Django application running!

::::{note}
Your Django application is now running with Gunicorn - a production-ready WSGI server. This is much more robust than Django's development server (`runserver`).
::::

### Step 5: Next Steps

Congratulations! You've successfully set up django-prodserver. Here's what to explore next:

- **Add background workers**: See {ref}`backend-celery-worker` for task processing
- **Deploy with Docker**: Check out the {ref}`guide-docker`
- **Environment configs**: Learn about {ref}`guide-environment-configs`
- **Choose a different backend**: Explore the {ref}`backend-reference`

---

(choosing-backend)=

## Choosing Your Backend

django-prodserver supports multiple backends for different use cases. Here's a quick guide to help you choose:

### Web Servers (WSGI/ASGI)

**Use {ref}`Gunicorn <backend-gunicorn>` for:**
- Traditional Django applications (synchronous)
- Production deployments on Linux servers
- Battle-tested reliability and performance

**Use {ref}`Uvicorn <backend-uvicorn-asgi>` for:**
- Async Django applications (Django 3.1+)
- WebSocket support
- Modern async/await views and middleware

**Use {ref}`Waitress <backend-waitress>` for:**
- Windows deployments
- Pure Python environments (no C dependencies)
- Simple production setups

**Use {ref}`Granian <backend-granian-asgi>` for:**
- Maximum performance (Rust-based)
- Both WSGI and ASGI support
- Modern production deployments

### Background Workers

**Use {ref}`Celery <backend-celery-worker>` for:**
- Distributed task processing
- Complex workflows and task chains
- Production-grade task queues with Redis/RabbitMQ

**Use {ref}`Django Tasks <backend-django-tasks>` for:**
- Simple background task processing
- No external dependencies (uses Django ORM)
- Lightweight deployments

**Use {ref}`Django-Q2 <backend-django-q2>` for:**
- ORM-backed task queues
- Scheduled tasks without external brokers
- Django-native task management

---

(your-first-server)=

## Your First Server

Here's a minimal working example using Gunicorn:

### 1. Install Dependencies

```bash
pip install django-prodserver gunicorn
```

### 2. Configure in settings.py

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    "django_prodserver",
]

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
        }
    }
}
```

### 3. Run the Server

```bash
python manage.py prodserver web
```

That's it! Your Django application is now running with Gunicorn on port 8000.

::::{tip}
**Development vs Production**: Use `python manage.py runserver` during development, and `python manage.py prodserver web` for production deployments.
::::

---

## Detailed Installation

### Package Installation

The package is published on [PyPI](https://pypi.org/project/django-prodserver/) and can be installed with `pip` (or any equivalent):

```bash
pip install django-prodserver
```

::::{note}
django-prodserver is a framework for managing production servers. You'll need to install the actual server backends separately (Gunicorn, Uvicorn, Celery, etc.).
::::

### Backend Installation

Install the backend you want to use:

```bash
# For Gunicorn (WSGI server)
pip install gunicorn

# For Uvicorn (ASGI server)
pip install uvicorn

# For Waitress (WSGI server, Windows-friendly)
pip install waitress

# For Granian (high-performance ASGI/WSGI)
pip install granian

# For Celery (distributed task queue)
pip install celery[redis]  # or celery[rabbitmq]

# For Django Tasks (Django 5.1+)
# Already included with Django 5.1+

# For Django-Q2 (ORM-backed queue)
pip install django-q2
```

See individual backend documentation pages for detailed installation instructions and requirements.

### Configuration

Add `django_prodserver` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_prodserver",
]
```

Add the `PRODUCTION_PROCESSES` setting to your `settings.py`. Below shows an example with a web process and worker process defined:

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

See {ref}`configuration-reference` for complete configuration documentation.

---

## Troubleshooting Installation

**ImportError: No module named 'gunicorn' (or other backend)**

You need to install the backend package separately:
```bash
pip install gunicorn  # or uvicorn, celery, etc.
```

**Django app not found in INSTALLED_APPS**

Make sure you've added `"django_prodserver"` to your `INSTALLED_APPS` list.

**PRODUCTION_PROCESSES setting not found**

Ensure you've added the `PRODUCTION_PROCESSES` dictionary to your Django settings file.

For more help, see the {ref}`troubleshooting` guide.

---

## Next Steps

- Read the {ref}`usage` guide to learn how to run your configured processes
- Explore {ref}`backend-reference` for detailed backend documentation
- Check out {ref}`practical-guides` for deployment tutorials
- See {ref}`configuration-reference` for advanced configuration options
