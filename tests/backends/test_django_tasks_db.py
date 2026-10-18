from unittest.mock import patch


def test_database_worker_import_and_compatibility():
    """Both import paths load the same database-specific worker."""
    from django.utils.module_loading import import_string

    new = import_string(
        "django_prodserver.backends.workers.django_tasks_db.DjangoTasksDBWorker"
    )
    old = import_string(
        "django_prodserver.backends.workers.django_tasks.DjangoTasksWorker"
    )
    assert old is new
    with patch("django.core.management.call_command") as command:
        new().start_server("--queues=default")
    command.assert_called_once_with("db_worker", "--queues=default")
