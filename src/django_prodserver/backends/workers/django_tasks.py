"""Compatibility import for the database-backed Django Tasks worker."""

from .django_tasks_db import DjangoTasksDBWorker

DjangoTasksWorker = DjangoTasksDBWorker

__all__ = ["DjangoTasksWorker"]
