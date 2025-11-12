(troubleshooting)=

# Troubleshooting Guide

Common issues and their solutions for django-prodserver deployments.

## Server Won't Start

### ImportError: No module named 'gunicorn' (or other backend)

**Symptom:**
```
ImportError: No module named 'gunicorn'
ModuleNotFoundError: No module named 'uvicorn'
```

**Cause:** Backend package not installed

**Solution:**
```bash
# Install the backend you're using
pip install gunicorn        # For Gunicorn
pip install uvicorn[standard]  # For Uvicorn
pip install granian         # For Granian
pip install waitress        # For Waitress
pip install celery[redis]   # For Celery
pip install django-q2       # For Django-Q2
```

::::{tip}
Always install backends in your production requirements.txt:
```
django-prodserver
gunicorn
celery[redis]
```
::::

### ImportError: django_prodserver not found

**Symptom:**
```
ModuleNotFoundError: No module named 'django_prodserver'
```

**Solution:**
```bash
pip install django-prodserver
```

And add to INSTALLED_APPS:
```python
INSTALLED_APPS = [
    # ...
    'django_prodserver',
]
```

### PRODUCTION_PROCESSES setting not found

**Symptom:**
```
ImproperlyConfigured: PRODUCTION_PROCESSES setting not found
```

**Solution:** Add PRODUCTION_PROCESSES to settings.py:
```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8000"}
    }
}
```

### Process name not found in PRODUCTION_PROCESSES

**Symptom:**
```
KeyError: 'web'
Process 'web' not found in PRODUCTION_PROCESSES
```

**Solution:** Ensure the process name matches your configuration:
```bash
# If you configured "web", use:
python manage.py prodserver web

# If you configured "worker", use:
python manage.py prodserver worker
```

Or check your PRODUCTION_PROCESSES dictionary has the correct key.

## Port and Binding Issues

### Port Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
[ERROR] Connection in use: ('0.0.0.0', 8000)
```

**Cause:** Another process is using the port

**Solution 1 - Find and stop the process:**
```bash
# On Linux/macOS
lsof -i :8000
kill <PID>

# On Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Solution 2 - Use a different port:**
```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {"bind": "0.0.0.0:8001"}  # Different port
    }
}
```

### Permission Denied on Port 80/443

**Symptom:**
```
PermissionError: [Errno 13] Permission denied
```

**Cause:** Ports below 1024 require root/admin privileges

**Solution 1 - Use higher port with reverse proxy:**
```python
"ARGS": {"bind": "0.0.0.0:8000"}  # Use port 8000
```

Then configure nginx/Apache to proxy to port 8000.

**Solution 2 - Run with sudo (not recommended):**
```bash
sudo python manage.py prodserver web
```

**Solution 3 - Grant capabilities (Linux only):**
```bash
sudo setcap 'cap_net_bind_service=+ep' /path/to/python
```

### Cannot Bind to 0.0.0.0

**Symptom:**
```
OSError: [Errno 99] Cannot assign requested address
```

**Solution:** Try binding to specific interface:
```python
"ARGS": {"bind": "127.0.0.1:8000"}  # Localhost only
# Or
"ARGS": {"host": "0.0.0.0"}  # All interfaces
```

## Configuration Issues

### Invalid BACKEND path

**Symptom:**
```
ImportError: Module django_prodserver.backends.gunicorn has no attribute 'GunicornServers'
```

**Cause:** Typo in BACKEND path

**Solution:** Use correct class name:
```python
# Correct
"BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"

# Common mistakes
# "GunicornServers" ❌
# "gunicorn.GunicornServer" ❌ (missing django_prodserver.backends)
# "django_prodserver.backends.gunicorn" ❌ (missing .GunicornServer)
```

### ARGS Not Being Applied

**Symptom:** Configuration in ARGS doesn't take effect

**Cause 1:** Wrong ARGS format

**Solution:** ARGS must be a dictionary:
```python
# Correct
"ARGS": {
    "bind": "0.0.0.0:8000",
    "workers": "4"
}

# Wrong
"ARGS": ["--bind", "0.0.0.0:8000"]  # ❌ List format
"ARGS": "--bind 0.0.0.0:8000"        # ❌ String format
```

**Cause 2:** Wrong argument names for backend

**Solution:** Check backend-specific ARGS:
- Gunicorn: `bind`, `workers`, `timeout`
- Uvicorn: `host`, `port`, `workers`
- Granian: `address`, `port`, `workers`

See {ref}`backend-reference` for correct ARGS for each backend.

### APP Configuration Missing (Celery)

**Symptom:**
```
TypeError: __init__() missing 1 required positional argument: 'APP'
```

**Cause:** Celery backends require APP configuration

**Solution:**
```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",  # Add this
        "ARGS": {}
    }
}
```

## Backend-Specific Issues

### Gunicorn Worker Timeout

**Symptom:**
```
[CRITICAL] WORKER TIMEOUT (pid:12345)
```

**Cause:** Request taking longer than timeout setting

**Solution:** Increase timeout:
```python
"ARGS": {
    "timeout": "120",  # Increase from default 30s
}
```

Or investigate slow requests.

### Uvicorn: ASGI Application Not Found

**Symptom:**
```
Error loading ASGI app. Import string "myproject.asgi:application" doesn't exist
```

**Solution 1:** Ensure asgi.py exists:
```python
# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
application = get_asgi_application()
```

**Solution 2:** Check DJANGO_SETTINGS_MODULE:
```bash
export DJANGO_SETTINGS_MODULE=myproject.settings
python manage.py prodserver web
```

### Celery: Broker Connection Failed

**Symptom:**
```
[ERROR] consumer: Cannot connect to redis://localhost:6379/0
ConnectionRefusedError: [Errno 111] Connection refused
```

**Cause:** Redis/RabbitMQ not running or wrong URL

**Solution 1:** Start broker:
```bash
# Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

**Solution 2:** Check CELERY_BROKER_URL:
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # Verify URL is correct
```

**Solution 3:** Test connection:
```bash
# Test Redis
redis-cli ping  # Should return PONG
```

### Celery: Tasks Not Discovered

**Symptom:** Tasks not being found or executed

**Solution 1:** Ensure autodiscover_tasks is called:
```python
# myproject/celery.py
app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()  # Add this
```

**Solution 2:** Create tasks.py in your apps:
```
myapp/
├── __init__.py
├── models.py
├── views.py
└── tasks.py  # Create this
```

**Solution 3:** Import Celery app in __init__.py:
```python
# myproject/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Waitress: Slow Performance

**Symptom:** Requests are slow

**Solution:** Increase threads:
```python
"ARGS": {
    "threads": "8",  # More threads
    "channel-timeout": "120",
}
```

### Granian: Installation Failed

**Symptom:**
```
error: can't find Rust compiler
```

**Solution:** Install pre-built wheel or Rust:
```bash
# Try upgrading pip and reinstalling
pip install --upgrade pip
pip install --upgrade granian

# Or install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Process Management Issues

### Process Won't Stop

**Symptom:** Process continues running after stop command

**Solution 1:** Send SIGTERM:
```bash
kill <PID>
```

**Solution 2:** Force kill (last resort):
```bash
kill -9 <PID>
```

**Solution 3:** Check for orphaned processes:
```bash
ps aux | grep prodserver
ps aux | grep gunicorn
pkill -f "prodserver web"
```

### Multiple Beat Instances Running

**Symptom:** Periodic tasks running multiple times

**Cause:** Multiple Celery Beat schedulers running

**Solution:** Ensure only ONE beat instance runs:
```bash
# Check for multiple beat processes
ps aux | grep "celery beat"

# Stop all
pkill -f "celery beat"

# Start only one
python manage.py prodserver beat
```

With systemd:
```ini
# Ensure beat service has no replicas
[Service]
Type=simple
# No --scale or replicas option
```

With Docker Compose:
```yaml
beat:
  deploy:
    replicas: 1  # Only 1!
```

### Worker Memory Leaks

**Symptom:** Workers consume increasing memory

**Solution:** Configure worker recycling:
```python
# Gunicorn
"ARGS": {
    "max-requests": "1000",
    "max-requests-jitter": "100",
}

# Celery
"ARGS": {
    "max-tasks-per-child": "1000",
    "max-memory-per-child": "500000",  # 500MB
}
```

## Performance Issues

### Slow Response Times

**Diagnosis:**
1. Check server logs
2. Monitor resource usage (CPU, memory)
3. Check database query performance
4. Profile your application code

**Solution 1:** Increase workers/concurrency:
```python
"ARGS": {
    "workers": "8",  # More workers
}
```

**Solution 2:** Use async/gevent for I/O-bound apps:
```python
# Gunicorn with gevent
"ARGS": {
    "worker-class": "gevent",
    "worker-connections": "1000",
}
```

**Solution 3:** Optimize database queries

**Solution 4:** Add caching (Redis, Memcached)

### High CPU Usage

**Diagnosis:**
```bash
top
htop
ps aux --sort=-pcpu | head
```

**Solution:** Reduce workers if CPU-bound:
```python
"ARGS": {
    "workers": "4",  # Fewer workers for CPU-bound tasks
}
```

### High Memory Usage

**Diagnosis:**
```bash
free -h
ps aux --sort=-rss | head
docker stats  # For containers
```

**Solution 1:** Reduce workers:
```python
"ARGS": {
    "workers": "2",  # Fewer workers
}
```

**Solution 2:** Set memory limits (systemd):
```ini
[Service]
MemoryLimit=2G
```

**Solution 3:** Set memory limits (Docker):
```yaml
deploy:
  resources:
    limits:
      memory: 2G
```

## Database Issues

### Database Connection Errors

**Symptom:**
```
OperationalError: could not connect to server
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution 1:** Verify database is running:
```bash
# PostgreSQL
pg_isready

# MySQL
mysqladmin ping
```

**Solution 2:** Check connection settings:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp',
        'USER': 'myapp',
        'PASSWORD': 'password',
        'HOST': 'localhost',  # Verify this
        'PORT': '5432',       # Verify this
    }
}
```

**Solution 3:** Test connection:
```bash
python manage.py dbshell
```

### Too Many Database Connections

**Symptom:**
```
OperationalError: FATAL:  sorry, too many clients already
```

**Solution:** Configure connection pooling:
```python
DATABASES = {
    'default': {
        # ...
        'CONN_MAX_AGE': 600,  # Keep connections for 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

And reduce workers:
```python
"ARGS": {
    "workers": "4",  # Fewer workers = fewer connections
}
```

## Docker-Specific Issues

### Container Exits Immediately

**Diagnosis:**
```bash
docker logs container_name
docker-compose logs web
```

**Common Causes:**
1. Missing dependencies
2. Configuration errors
3. Port binding issues
4. Database not ready

**Solution:** Use entrypoint script with wait logic:
```bash
#!/bin/bash
# Wait for database
while ! nc -z db 5432; do
  sleep 0.1
done
python manage.py prodserver web
```

### Cannot Connect to Database from Container

**Solution:** Use service name as host:
```python
# In Docker Compose
DATABASES = {
    'default': {
        'HOST': 'db',  # Service name, not 'localhost'
    }
}
```

### Static Files Not Found

**Solution:** Collect static files in Dockerfile:
```dockerfile
RUN python manage.py collectstatic --noinput
```

And mount volume:
```yaml
volumes:
  - ./staticfiles:/app/staticfiles
```

## Environment Issues

### Wrong Settings File Loaded

**Symptom:** Development settings loaded in production

**Solution:** Set DJANGO_SETTINGS_MODULE:
```bash
export DJANGO_SETTINGS_MODULE=myproject.settings.prod
python manage.py prodserver web
```

Or use --settings flag:
```bash
python manage.py prodserver web --settings=myproject.settings.prod
```

### Environment Variables Not Loaded

**Solution 1:** Export before running:
```bash
export DEBUG=False
export DATABASE_URL=postgres://...
python manage.py prodserver web
```

**Solution 2:** Use .env file with python-dotenv:
```bash
pip install python-dotenv
```

```python
# settings.py
from dotenv import load_dotenv
load_dotenv()
```

## Getting More Help

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Django Configuration

```bash
python manage.py check
python manage.py check --deploy  # Production checks
```

### View Process Information

```bash
# Process list
ps aux | grep prodserver

# Ports in use
netstat -tulpn | grep python
lsof -i -P -n | grep python

# Resource usage
top -p <PID>
```

### File a Bug Report

If you've tried everything and still have issues:

1. Search existing issues: https://github.com/nanorepublica/django-prodserver/issues
2. Create new issue with:
   - Django version
   - django-prodserver version
   - Backend and version
   - Full error message
   - Configuration (sanitized)
   - Steps to reproduce

## Quick Reference

### Common Commands

```bash
# Check installation
pip show django-prodserver

# Test configuration
python manage.py check

# Run with debug logging
python manage.py prodserver web --verbosity 3

# Test specific settings
python manage.py prodserver web --settings=myproject.settings.staging
```

### Useful Debugging Tools

```bash
# Check running processes
ps aux | grep python

# Check ports
lsof -i :8000
netstat -tulpn | grep 8000

# Monitor resources
top
htop
docker stats

# View logs
tail -f /var/log/myapp/*.log
journalctl -u myapp-web -f
docker-compose logs -f web
```

## Related Documentation

- {ref}`configuration-reference` - Configuration reference
- {ref}`backend-reference` - Backend-specific documentation
- {ref}`usage` - Usage patterns
- {ref}`practical-guides` - Deployment guides
