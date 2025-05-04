(usage)=

# Usage

Once the `PRODUCTION_PROCESSES` setting has been configured you can then start the processes as follows:

```sh
python manage.py prodserver web
```

```sh
python manage.py prodserver worker
```

More generically this this is of the form:

```sh
python manage.py prodserver <process_name>
```

# Creating a new backend.

Creating a backend is fairly simple. Subclass the `BaseServerBackend` class, then implement
the `start_server` method which should call the underlying process in the best possible way for a production
setting. You can also optionally override `prep_server_args` method to aid with this to provide any default arguments
or formatting to the `start_server` command.

See `django_prodserver.backends` for examples of existing backends for inspiration. Pull Request's are welcome for
additional backends.
