(troubleshooting)=

# Troubleshooting

## Startup Issues

### ImportError: No module named 'gunicorn'

Install the backend:

```bash
pip install django-prodserver[gunicorn]  # or uvicorn, celery, etc.
```

### PRODUCTION_PROCESSES not found

Add to `settings.py`:

```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"},
    }
}
```

### Process name not found

Ensure the process name matches your config:

```bash
# If configured as "web":
python manage.py prodserver web
```

---

## Port Issues

### Port already in use

```bash
# Find and stop the process
lsof -i :8000
kill <PID>

# Or use a different port
"ARGS": {"bind": "0.0.0.0:8001"}
```

### Permission denied on port 80/443

Use a higher port with a reverse proxy, or:

```bash
# Linux only
sudo setcap 'cap_net_bind_service=+ep' /path/to/python
```

---

## Backend Issues

### Gunicorn: Worker timeout

Increase timeout:

```python
"ARGS": {"timeout": "120"}
```

### Uvicorn: ASGI app not found

Ensure `asgi.py` exists:

```python
# myproject/asgi.py
from django.core.asgi import get_asgi_application
application = get_asgi_application()
```

### Celery: Broker connection failed

```bash
# Verify Redis is running
redis-cli ping

# Check CELERY_BROKER_URL
CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

### Celery: Tasks not discovered

```python
# myproject/celery.py
app.autodiscover_tasks()

# myproject/__init__.py
from .celery import app as celery_app
__all__ = ('celery_app',)
```

---

## Performance Issues

### High memory usage

Reduce workers and enable recycling:

```python
# Gunicorn
"ARGS": {"workers": "2", "max-requests": "1000"}

# Celery
"ARGS": {"max-tasks-per-child": "1000"}
```

### Slow response times

- Increase workers/concurrency
- Check database query performance
- Add caching

---

## Database Issues

### Too many connections

```python
DATABASES = {
    'default': {
        'CONN_MAX_AGE': 600,  # Reuse connections
    }
}
```

And reduce worker count.

---

## Docker Issues

### Container exits immediately

Check logs:

```bash
docker logs container_name
```

Use health checks and wait for dependencies.

### Can't connect to database

Use service name as host:

```python
DATABASES = {'default': {'HOST': 'db'}}  # Not 'localhost'
```

---

## Debugging

```bash
# Check installation
pip show django-prodserver

# Validate config
python manage.py check

# Verbose output
python manage.py prodserver web --verbosity 3

# Check processes
ps aux | grep python
lsof -i :8000
```

---

## Getting Help

1. Search [existing issues](https://github.com/nanorepublica/django-prodserver/issues)
2. Include: Django version, django-prodserver version, backend, full error, config

---

## Related

- {ref}`configuration-reference`
- {ref}`backend-reference`
