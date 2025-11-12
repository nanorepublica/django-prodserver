(guide-backend-switching)=

# Backend Switching Guide

Learn how to migrate between different backends (Gunicorn to Uvicorn, Celery to Django Tasks, etc.) with step-by-step instructions and configuration examples.

## Overview

django-prodserver makes it easy to switch backends by simply changing configuration. This guide covers common migration scenarios and provides migration checklists.

## Why Switch Backends?

Common reasons to switch:
- **Performance**: Need better throughput or lower latency
- **Features**: Require async support, WebSockets, or specific capabilities
- **Simplicity**: Move to simpler solution for easier maintenance
- **Platform**: Deploy to different operating system (Linux to Windows)
- **Cost**: Reduce infrastructure dependencies

## Migration Strategies

### Strategy 1: Blue-Green Deployment

1. Deploy new backend alongside old one
2. Test thoroughly
3. Switch traffic to new backend
4. Keep old backend as backup
5. Remove old backend after stabilization

### Strategy 2: Gradual Migration

1. Update configuration
2. Deploy to staging first
3. Test extensively
4. Deploy to production
5. Monitor and rollback if needed

## Web Server Migrations

### Gunicorn → Uvicorn (Adding Async Support)

**When**: You want to use async views, WebSockets, or ASGI features

**Before (Gunicorn - WSGI):**
```python
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

**After (Uvicorn - ASGI):**
```python
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "4",
            "timeout-keep-alive": "60",
        }
    }
}
```

**Migration Steps:**

1. **Install Uvicorn:**
   ```bash
   pip install uvicorn[standard]
   ```

2. **Verify ASGI configuration:**
   ```python
   # Ensure asgi.py exists and is correct
   # myproject/asgi.py
   import os
   from django.core.asgi import get_asgi_application

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
   application = get_asgi_application()
   ```

3. **Update configuration** (as shown above)

4. **Test in staging:**
   ```bash
   python manage.py prodserver web --settings=myproject.settings.staging
   ```

5. **Deploy to production**

**Considerations:**
- ARGS mapping differs (bind → host/port)
- Fewer workers needed with async (1-2 per CPU)
- Monitor performance and adjust

### Gunicorn → Granian (Performance Upgrade)

**When**: You want Rust-powered performance while keeping WSGI

**Before (Gunicorn):**
```python
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

**After (Granian WSGI):**
```python
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

**Migration Steps:**

1. **Install Granian:**
   ```bash
   pip install granian
   ```

2. **Update configuration**

3. **Tune threads** (Granian-specific)

4. **Test and deploy**

### Waitress → Gunicorn (Windows → Linux)

**When**: Migrating from Windows to Linux servers

**Before (Waitress - Windows):**
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

**After (Gunicorn - Linux):**
```python
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

**Migration Steps:**

1. **Prepare Linux environment**

2. **Install Gunicorn:**
   ```bash
   pip install gunicorn
   ```

3. **Update configuration**

4. **Test on Linux staging server**

5. **Migrate production**

## Worker Migrations

### Celery → Django Tasks (Simplification)

**When**: Reducing complexity, removing Redis/RabbitMQ dependency

**Before (Celery):**
```python
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'

PRODUCTION_PROCESSES = {
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
        "ARGS": {}
    }
}
```

**After (Django Tasks - Django 5.1+):**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django.contrib.tasks',
]

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "4",
        }
    }
}
```

**Migration Steps:**

1. **Ensure Django 5.1+:**
   ```bash
   pip install "django>=5.1"
   ```

2. **Add to INSTALLED_APPS**

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Convert tasks:**
   ```python
   # Before (Celery)
   from celery import shared_task

   @shared_task
   def send_email(email):
       # ...

   # After (Django Tasks)
   from django.contrib.tasks import task

   @task()
   def send_email(email):
       # ...
   ```

5. **Update task calls** (unchanged):
   ```python
   send_email.delay('user@example.com')
   ```

6. **Test thoroughly** (some Celery features not available)

7. **Remove Celery and broker**

**Limitations:**
- No chains, groups, or chords
- Database-backed (less performant at scale)
- Simpler feature set

### Django Tasks → Celery (Scaling Up)

**When**: Need distributed processing, complex workflows, or high volume

**Before (Django Tasks):**
```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "2",
        }
    }
}
```

**After (Celery):**
```python
# Requires broker setup
CELERY_BROKER_URL = 'redis://localhost:6379/0'

PRODUCTION_PROCESSES = {
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
        "ARGS": {}
    }
}
```

**Migration Steps:**

1. **Set up broker** (Redis or RabbitMQ)

2. **Install Celery:**
   ```bash
   pip install celery[redis]
   ```

3. **Create Celery app** (see {ref}`backend-celery-worker`)

4. **Convert tasks** (decorator change)

5. **Update configuration**

6. **Test with broker**

7. **Deploy**

### Celery → Django-Q2 (ORM-backed Alternative)

**When**: Want more features than Django Tasks but simpler than Celery

**Before (Celery):**
```python
PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {"concurrency": "4"}
    }
}
```

**After (Django-Q2):**
```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django_q',
]

Q_CLUSTER = {
    'name': 'myproject',
    'workers': 4,
    'timeout': 90,
}

PRODUCTION_PROCESSES = {
    "worker": {
        "BACKEND": "django_prodserver.backends.django_q2.DjangoQ2Worker",
        "ARGS": {"verbosity": "1"}
    }
}
```

**Migration Steps:**

1. **Install Django-Q2:**
   ```bash
   pip install django-q2
   ```

2. **Add to INSTALLED_APPS**

3. **Run migrations**

4. **Convert tasks:**
   ```python
   # Before (Celery)
   from celery import shared_task

   @shared_task
   def process_data(data_id):
       # ...

   # After (Django-Q2)
   def process_data(data_id):
       # Regular function, no decorator

   # Enqueue differently
   from django_q.tasks import async_task
   async_task('myapp.tasks.process_data', data_id)
   ```

5. **Test**

6. **Remove Celery and broker**

## Migration Checklist

### Pre-Migration

- [ ] Read new backend documentation
- [ ] Understand ARGS differences
- [ ] Test in local development
- [ ] Test in staging environment
- [ ] Prepare rollback plan
- [ ] Document configuration changes
- [ ] Brief team on changes

### During Migration

- [ ] Update dependencies (requirements.txt)
- [ ] Update configuration (settings.py)
- [ ] Convert tasks if needed
- [ ] Update environment variables
- [ ] Update Docker/systemd configs
- [ ] Deploy to staging
- [ ] Run integration tests
- [ ] Monitor performance
- [ ] Fix any issues

### Post-Migration

- [ ] Deploy to production
- [ ] Monitor logs and errors
- [ ] Check performance metrics
- [ ] Verify all features work
- [ ] Update documentation
- [ ] Clean up old dependencies
- [ ] Remove old configuration

## Testing Your Migration

### Functionality Tests

```python
# Test web server
curl http://localhost:8000/
curl http://localhost:8000/admin/

# Test task processing
python manage.py shell
>>> from myapp.tasks import my_task
>>> my_task.delay()
```

### Performance Tests

```bash
# Load testing with apache bench
ab -n 1000 -c 10 http://localhost:8000/

# Monitor resource usage
top
htop
docker stats
```

### Rollback Plan

Keep old configuration for quick rollback:

```python
# settings.py
USE_NEW_BACKEND = os.getenv('USE_NEW_BACKEND', 'False') == 'True'

if USE_NEW_BACKEND:
    PRODUCTION_PROCESSES = {
        # New backend config
    }
else:
    PRODUCTION_PROCESSES = {
        # Old backend config
    }
```

## Common Issues

### ARGS Not Working

**Problem**: Configuration not being applied

**Solution**: Check ARGS mapping for new backend
- Different backends use different argument names
- Consult backend-specific documentation

### Performance Regression

**Problem**: New backend is slower

**Solution**: Tune configuration
- Adjust worker/thread counts
- Check resource limits
- Monitor bottlenecks

### Features Missing

**Problem**: Feature worked in old backend but not new one

**Solution**: Check feature compatibility
- Read limitations in backend documentation
- Consider alternative approaches
- May need to keep old backend for specific features

## Related Documentation

- {ref}`backend-reference` - All backend documentation
- {ref}`configuration-reference` - Configuration reference
- {ref}`guide-environment-configs` - Environment configuration
- {ref}`troubleshooting` - Troubleshooting guide
