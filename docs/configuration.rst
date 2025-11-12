.. _configuration-reference:

Configuration
=============

Complete reference for configuring django-prodserver using the ``PRODUCTION_PROCESSES`` setting.

Overview
--------

django-prodserver is configured entirely through Django settings using the ``PRODUCTION_PROCESSES`` dictionary. This dictionary defines all the production processes (web servers, workers, schedulers) that your application needs.

.. code-block:: python

    # settings.py
    PRODUCTION_PROCESSES = {
        "process_name": {
            "BACKEND": "path.to.backend.class",
            "APP": "optional.app.path",  # Only for some backends
            "ARGS": {
                "arg_name": "value",
            }
        }
    }

Basic Structure
---------------

``PRODUCTION_PROCESSES`` Dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The top-level ``PRODUCTION_PROCESSES`` dictionary maps process names to their configurations:

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web": {...},      # Web server process
        "worker": {...},   # Background worker process
        "beat": {...},     # Scheduler process
    }

**Process names** are arbitrary and can be anything you want. Common conventions:

- ``web`` - Web server (Gunicorn, Uvicorn, etc.)
- ``api`` - API server (if separate from web)
- ``worker`` - Background task worker
- ``beat`` - Scheduled task runner
- ``priority_worker`` - High-priority task worker

Process Configuration Keys
---------------------------

Each process configuration dictionary supports the following keys:

BACKEND (Required)
~~~~~~~~~~~~~~~~~~

The Python import path to the backend class:

.. code-block:: python

    "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"

**Available backends:**

**WSGI Servers:**

- ``django_prodserver.backends.gunicorn.GunicornServer``
- ``django_prodserver.backends.waitress.WaitressServer``
- ``django_prodserver.backends.granian.GranianWSGIServer``

**ASGI Servers:**

- ``django_prodserver.backends.uvicorn.UvicornServer``
- ``django_prodserver.backends.uvicorn.UvicornWSGIServer``
- ``django_prodserver.backends.granian.GranianASGIServer``

**Workers:**

- ``django_prodserver.backends.celery.CeleryWorker``
- ``django_prodserver.backends.celery.CeleryBeat``
- ``django_prodserver.backends.django_tasks.DjangoTasksWorker``
- ``django_prodserver.backends.django_q2.DjangoQ2Worker``

See :ref:`backend-reference` for detailed backend documentation.

APP (Optional)
~~~~~~~~~~~~~~

The Python import path to an application instance. Required for Celery backends:

.. code-block:: python

    "APP": "myproject.celery.app"

**Used by:**

- **Celery Worker** and **Celery Beat**: Path to Celery app instance
- Other custom backends may use this field

.. _args-translation:

ARGS (Optional)
~~~~~~~~~~~~~~~

A dictionary of arguments passed to the backend. These are automatically converted to command-line arguments:

.. code-block:: python

    "ARGS": {
        "bind": "0.0.0.0:8000",
        "workers": "4",
        "timeout": "30"
    }

This translates to::

    --bind=0.0.0.0:8000 --workers=4 --timeout=30

**How ARGS Translation Works:**

1. Dictionary keys become argument names (with ``--`` prefix)
2. Dictionary values become argument values (with ``=`` separator)
3. Arguments are passed directly to the underlying backend

**Example Translation:**

.. code-block:: python

    # Settings configuration
    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": "0.0.0.0:8000",
                "workers": "4",
                "worker-class": "sync",
                "timeout": "60"
            }
        }
    }

    # Translates to CLI command:
    # gunicorn --bind=0.0.0.0:8000 --workers=4 --worker-class=sync --timeout=60

**Available arguments vary by backend.** See individual backend documentation:

- :ref:`backend-gunicorn` - Gunicorn ARGS
- :ref:`backend-uvicorn-asgi` - Uvicorn ARGS
- :ref:`backend-celery-worker` - Celery ARGS

Complete Configuration Examples
--------------------------------

Single Web Server
~~~~~~~~~~~~~~~~~

Basic Gunicorn web server:

.. code-block:: python

    # settings.py
    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": "0.0.0.0:8000",
                "workers": "4"
            }
        }
    }

Web Server + Background Worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Web server with Celery worker for background tasks:

.. code-block:: python

    # settings.py
    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": "0.0.0.0:8000",
                "workers": "4",
                "timeout": "60"
            }
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "concurrency": "4",
                "loglevel": "info"
            }
        }
    }

Complete Application Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Web server + worker + scheduler:

.. code-block:: python

    # settings.py
    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
            "ARGS": {
                "host": "0.0.0.0",
                "port": "8000",
                "workers": "4",
                "log-level": "info"
            }
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "concurrency": "4",
                "loglevel": "info",
                "max-tasks-per-child": "1000"
            }
        },
        "beat": {
            "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
            "APP": "myproject.celery.app",
            "ARGS": {
                "loglevel": "info"
            }
        }
    }

Environment-Specific Configuration
-----------------------------------

Use Django's settings module pattern for different environments:

Development Settings
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # settings_dev.py
    from .settings import *

    DEBUG = True

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.waitress.WaitressServer",
            "ARGS": {
                "port": "8000",
                "threads": "4"
            }
        }
    }

Staging Settings
~~~~~~~~~~~~~~~~

.. code-block:: python

    # settings_staging.py
    from .settings import *

    DEBUG = False
    ALLOWED_HOSTS = ['staging.example.com']

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": "0.0.0.0:8000",
                "workers": "2",
                "timeout": "60",
                "access-logfile": "/var/log/myapp/access.log"
            }
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "concurrency": "2",
                "loglevel": "debug"
            }
        }
    }

Production Settings
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # settings_prod.py
    from .settings import *

    DEBUG = False
    ALLOWED_HOSTS = ['example.com', 'www.example.com']

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
                "error-logfile": "/var/log/myapp/error.log"
            }
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "concurrency": "8",
                "loglevel": "info",
                "max-tasks-per-child": "1000"
            }
        },
        "beat": {
            "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
            "APP": "myproject.celery.app",
            "ARGS": {
                "loglevel": "info"
            }
        }
    }

Using Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine with environment variables for flexibility:

.. code-block:: python

    # settings.py
    import os

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": f"0.0.0.0:{os.getenv('PORT', '8000')}",
                "workers": os.getenv('WEB_WORKERS', '4'),
                "timeout": os.getenv('WEB_TIMEOUT', '60')
            }
        }
    }

See :ref:`guide-environment-configs` for more environment configuration patterns.

Advanced Configuration Patterns
--------------------------------

Multiple Workers for Different Queues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run separate workers for different task priorities:

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8000"}
        },
        "default_worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "queues": "default",
                "concurrency": "4"
            }
        },
        "priority_worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {
                "queues": "priority",
                "concurrency": "2"
            }
        }
    }

Multiple Ports
~~~~~~~~~~~~~~

Run multiple web server instances on different ports:

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web_8000": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8000"}
        },
        "web_8001": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8001"}
        }
    }

Mixed Backend Types
~~~~~~~~~~~~~~~~~~~

Use different backends for different purposes:

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8000"}
        },
        "websocket": {
            "BACKEND": "django_prodserver.backends.uvicorn.UvicornServer",
            "ARGS": {
                "host": "0.0.0.0",
                "port": "8001"
            }
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {"concurrency": "4"}
        }
    }

Configuration Best Practices
-----------------------------

1. **Use environment-specific settings files**

   Separate ``settings_dev.py``, ``settings_staging.py``, ``settings_prod.py``

2. **Use environment variables for secrets**

   Never hardcode sensitive values like API keys or database passwords

3. **Start with conservative worker counts**

   Begin with ``workers = CPU_count * 2 + 1`` and adjust based on monitoring

4. **Set appropriate timeouts**

   Configure timeouts based on your application's needs (default: 30s)

5. **Use process supervision**

   Run processes with systemd, Supervisor, or Docker for automatic restarts

6. **Test configuration changes**

   Always test configuration changes in staging before production

7. **Monitor resource usage**

   Watch CPU, memory, and connection counts to tune worker settings

8. **Log appropriately**

   Balance log verbosity with storage and performance needs

Common Configuration Mistakes
------------------------------

.. warning::

   **Port conflicts:** Ensure each process uses a unique port

   **Missing APP configuration:** Celery backends require the ``APP`` key

   **Too many workers:** More workers isn't always better; monitor resource usage

   **Incorrect BACKEND path:** Use full Python import path to backend class

   **Missing backend installation:** Install backend packages (gunicorn, celery, etc.)

Validation and Debugging
-------------------------

Django checks your ``PRODUCTION_PROCESSES`` configuration when you run the management command. Common validation errors:

**"PRODUCTION_PROCESSES setting not found"**

- Add ``PRODUCTION_PROCESSES`` dictionary to your settings file

**"Process 'name' not found in PRODUCTION_PROCESSES"**

- Check that the process name matches your configuration
- Verify you're using the correct settings file

**"Cannot import BACKEND"**

- Verify the backend path is correct
- Ensure the backend package is installed (``pip install gunicorn``)

**"Invalid ARGS configuration"**

- ARGS must be a dictionary
- Values should be strings or numbers

See :ref:`troubleshooting` for more debugging help.

API Documentation
-----------------

.. automodule:: django_prodserver.conf
   :noindex:

.. autoclass:: AppSettings()
  :members:

Next Steps
----------

- See :ref:`backend-reference` for backend-specific ARGS documentation
- Read :ref:`guide-environment-configs` for environment configuration examples
- Check :ref:`usage` for running configured processes
- Review :ref:`troubleshooting` for common issues
