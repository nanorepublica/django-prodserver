.. _configuration-reference:

Configuration
=============

django-prodserver is configured through the ``PRODUCTION_PROCESSES`` setting.

Basic Structure
---------------

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "process_name": {
            "BACKEND": "path.to.backend.class",
            "APP": "optional.app.path",  # Required for Celery
            "ARGS": {"arg_name": "value"},
        }
    }

Configuration Keys
------------------

BACKEND (Required)
~~~~~~~~~~~~~~~~~~

Python import path to the backend class:

.. code-block:: python

    "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer"

**Available backends:**

+--------------------------------------------------+-------------+
| Backend Class                                    | Type        |
+==================================================+=============+
| ``django_prodserver.backends.gunicorn.GunicornServer``    | WSGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.waitress.WaitressServer``    | WSGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.granian.GranianWSGIServer``  | WSGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.uvicorn.UvicornServer``      | ASGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.uvicorn.UvicornWSGIServer``  | WSGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.granian.GranianASGIServer``  | ASGI        |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.celery.CeleryWorker``        | Worker      |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.celery.CeleryBeat``          | Scheduler   |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.django_tasks.DjangoTasksWorker`` | Worker  |
+--------------------------------------------------+-------------+
| ``django_prodserver.backends.django_q2.DjangoQ2Worker``   | Worker      |
+--------------------------------------------------+-------------+

APP (Celery only)
~~~~~~~~~~~~~~~~~

Path to Celery app instance:

.. code-block:: python

    "APP": "myproject.celery.app"

.. _args-translation:

ARGS
~~~~

Arguments passed to the backend, converted to CLI flags:

.. code-block:: python

    "ARGS": {
        "bind": "0.0.0.0:8000",      # --bind=0.0.0.0:8000
        "workers": "4",               # --workers=4
    }

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

See :ref:`backend-reference` for backend-specific ARGS.

Complete Configuration Examples
--------------------------------

Single Web Server
~~~~~~~~~~~~~~~~~

Basic Gunicorn web server:

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
        }
    }

Web + Worker + Beat
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {"bind": "0.0.0.0:8000", "workers": "4"},
        },
        "worker": {
            "BACKEND": "django_prodserver.backends.celery.CeleryWorker",
            "APP": "myproject.celery.app",
            "ARGS": {"concurrency": "4", "loglevel": "info"},
        },
        "beat": {
            "BACKEND": "django_prodserver.backends.celery.CeleryBeat",
            "APP": "myproject.celery.app",
            "ARGS": {"loglevel": "info"},
        },
    }

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import os

    PRODUCTION_PROCESSES = {
        "web": {
            "BACKEND": "django_prodserver.backends.gunicorn.GunicornServer",
            "ARGS": {
                "bind": f"0.0.0.0:{os.getenv('PORT', '8000')}",
                "workers": os.getenv('WEB_WORKERS', '4'),
            },
        }
    }

Best Practices
--------------

1. Use environment-specific settings files (``settings_dev.py``, ``settings_prod.py``)
2. Use environment variables for deployment-specific values
3. Start with ``workers = CPU_count * 2 + 1`` and tune based on monitoring
4. Set appropriate timeouts for your application
5. Use process supervision (systemd, Docker) for automatic restarts

Common Mistakes
---------------

.. warning::

   - **Port conflicts:** Each process needs a unique port
   - **Missing APP:** Celery backends require the ``APP`` key
   - **Wrong BACKEND path:** Use full import path including class name
   - **Missing backend package:** Install gunicorn, celery, etc.

API Documentation
-----------------

.. automodule:: django_prodserver.conf
   :noindex:

.. autoclass:: AppSettings()
  :members:

Next Steps
----------

- :ref:`backend-reference` - Backend-specific ARGS
- :ref:`usage` - Running processes
- :ref:`troubleshooting` - Common issues
