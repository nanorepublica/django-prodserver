(guide-environment-configs)=

# Environment-Specific Configuration

Learn how to manage different configurations across development, staging, and production environments using Django settings patterns and environment variables.

## Overview

Different environments require different configurations:
- **Development**: Debug enabled, fewer workers, verbose logging
- **Staging**: Production-like settings for testing
- **Production**: Optimized for performance and security

## Django Settings Patterns

### Pattern 1: Separate Settings Files

The most common approach - separate files for each environment.

#### Directory Structure

```
myproject/
├── settings/
│   ├── __init__.py
│   ├── base.py        # Shared settings
│   ├── dev.py         # Development
│   ├── staging.py     # Staging
│   └── prod.py        # Production
└── manage.py
```

#### Base Settings

```python
# myproject/settings/base.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Apps common to all environments
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps
    'django_prodserver',
]

# Middleware, templates, etc.
MIDDLEWARE = [...]
TEMPLATES = [...]

# Default database (override in environment files)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp',
    }
}
```

#### Development Settings

```python
# myproject/settings/dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Development database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Simple dev server
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "threads": "2",
        }
    }
}

# Email to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

#### Staging Settings

```python
# myproject/settings/staging.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['staging.example.com']

# Staging database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'myapp_staging',
        'USER': 'myapp',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'staging-db.example.com',
        'PORT': '5432',
    }
}

# Staging configuration - similar to production but with debug features
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "2",
            "timeout": "60",
            "loglevel": "debug",  # More verbose logging
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "2",
            "loglevel": "debug",
        }
    }
}

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://staging-redis:6379/0')
```

#### Production Settings

```python
# myproject/settings/prod.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['example.com', 'www.example.com']

# Production database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

# Production server configuration
PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "8",
            "worker-class": "gevent",
            "timeout": "120",
            "max-requests": "1000",
            "max-requests-jitter": "100",
            "access-logfile": "/var/log/myapp/access.log",
            "error-logfile": "/var/log/myapp/error.log",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "8",
            "loglevel": "info",
            "max-tasks-per-child": "1000",
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

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

#### Usage

```bash
# Development
python manage.py runserver --settings=myproject.settings.dev

# Staging
python manage.py prodserver web --settings=myproject.settings.staging

# Production
python manage.py prodserver web --settings=myproject.settings.prod
```

Or set the `DJANGO_SETTINGS_MODULE` environment variable:

```bash
# In your shell or systemd service file
export DJANGO_SETTINGS_MODULE=myproject.settings.prod
python manage.py prodserver web
```

### Pattern 2: Single File with Environment Variables

Use a single settings file with environment variable controls.

```python
# settings.py
import os

# Environment selection
ENV = os.getenv('DJANGO_ENV', 'development')
DEBUG = ENV == 'development'

if ENV == 'production':
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
else:
    ALLOWED_HOSTS = ['*']

# Database configuration from environment
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'myapp'),
        'USER': os.getenv('DB_USER', 'myapp'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Environment-specific configurations
if ENV == 'production':
    WEB_WORKERS = os.getenv('WEB_WORKERS', '8')
    WORKER_CONCURRENCY = os.getenv('WORKER_CONCURRENCY', '8')
elif ENV == 'staging':
    WEB_WORKERS = os.getenv('WEB_WORKERS', '4')
    WORKER_CONCURRENCY = os.getenv('WORKER_CONCURRENCY', '4')
else:  # development
    WEB_WORKERS = os.getenv('WEB_WORKERS', '2')
    WORKER_CONCURRENCY = os.getenv('WORKER_CONCURRENCY', '2')

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": f"0.0.0.0:{os.getenv('PORT', '8000')}",
            "workers": WEB_WORKERS,
            "timeout": os.getenv('WEB_TIMEOUT', '60'),
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": WORKER_CONCURRENCY,
        }
    }
}
```

## Environment Variables Management

### Using python-dotenv

Install python-dotenv:

```bash
pip install python-dotenv
```

Create environment files:

```bash
# .env.development
DJANGO_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

```bash
# .env.production
DJANGO_ENV=production
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:pass@host/db
ALLOWED_HOSTS=example.com,www.example.com
WEB_WORKERS=8
WORKER_CONCURRENCY=8
```

Load in settings:

```python
# settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment file
ENV_FILE = Path(__file__).resolve().parent.parent / f'.env.{os.getenv("DJANGO_ENV", "development")}'
load_dotenv(ENV_FILE)

# Now use os.getenv() as normal
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

### Using django-environ

```bash
pip install django-environ
```

```python
# settings.py
import environ

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)

# Read .env file
environ.Env.read_env()

DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')
DATABASES = {
    'default': env.db(),
}

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": f"0.0.0.0:{env('PORT', default=8000)}",
            "workers": env('WEB_WORKERS', default='4'),
        }
    }
}
```

## Configuration Examples by Environment

### Development Configuration

Focus: Easy debugging, fast iteration

```python
DEBUG = True
ALLOWED_HOSTS = ['*']

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
        "ARGS": {
            "host": "127.0.0.1",
            "port": "8000",
            "threads": "2",
        }
    },
    # Lightweight task queue for development
    "worker": {
        "BACKEND": "django_prodserver.backends.django_tasks.DjangoTasksWorker",
        "ARGS": {
            "processes": "1",
        }
    }
}

# Console email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Staging Configuration

Focus: Production-like testing environment

```python
DEBUG = False
ALLOWED_HOSTS = ['staging.example.com']

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
        "ARGS": {
            "bind": "0.0.0.0:8000",
            "workers": "4",
            "timeout": "60",
            "loglevel": "debug",
            "access-logfile": "-",  # Log to stdout
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "4",
            "loglevel": "debug",
        }
    },
    "beat": {
        "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
        "APP": "myproject.celery.app",
        "ARGS": {
            "loglevel": "debug",
        }
    }
}
```

### Production Configuration

Focus: Performance, security, reliability

```python
DEBUG = False
ALLOWED_HOSTS = ['example.com', 'www.example.com']

PRODUCTION_PROCESSES = {
    "web": {
        "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
        "ARGS": {
            "host": "0.0.0.0",
            "port": "8000",
            "workers": "8",
            "loop": "uvloop",
            "limit-concurrency": "1000",
            "log-level": "warning",
        }
    },
    "worker": {
        "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
        "APP": "myproject.celery.app",
        "ARGS": {
            "concurrency": "8",
            "loglevel": "info",
            "max-tasks-per-child": "1000",
            "max-memory-per-child": "500000",
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

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Best Practices

1. **Never commit secrets**: Use environment variables for sensitive data
2. **Use .gitignore**: Exclude .env files from version control
3. **Document environment variables**: Create .env.example as template
4. **Test staging like production**: Make staging as close to production as possible
5. **Use consistent naming**: Follow naming conventions for environment variables
6. **Validate configuration**: Check required settings on startup
7. **Monitor configuration changes**: Log configuration on startup (excluding secrets)

## Related Documentation

- {ref}`configuration-reference` - Complete PRODUCTION_PROCESSES reference
- {ref}`guide-docker` - Docker environment configuration
- {ref}`guide-multi-process` - Running multiple processes
- {ref}`troubleshooting` - Common configuration issues
