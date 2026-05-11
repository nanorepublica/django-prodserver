# Raw Idea

> Captured from conversation on 2026-05-11.

I would like to explore what it would look like to split the package into multiple
repos. The purpose here is to have a **core package** with the goal of eventually
being **merged into Django** with some of the backends, while other backends would
ideally be **merged into their respective upstream repos** (gunicorn, uvicorn,
django-tasks, django-q2, celery, ...) or **sit in a separate repo** that lets a
developer opt in to them.

Implementation note from the requester: each structural option should be explored
on its own branch so the trade-offs can be compared with real code, not just on
paper. This spec is therefore written as a set of parallel exploration tracks
rather than a single linear plan.
