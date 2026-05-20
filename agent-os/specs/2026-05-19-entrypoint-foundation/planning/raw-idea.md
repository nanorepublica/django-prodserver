# Raw Idea

> Captured from conversation on 2026-05-19.

This is the **Phase 0** prerequisite carved out of the parent spec
`2026-05-11-split-package-into-multiple-repos`. The parent spec evaluates how to
split django-prodserver across multiple packages/repos; Phase 0 is the
non-breaking foundation that has to land *before* any split spike begins:

> "Also by the looks of it, we should just do option C as a prerequisite anyway.
> Um or at least make a plan for option C as a prerequisite before anything
> else."

Phase 0 delivers:

1. `importlib.metadata` entry-point–based backend discovery (closes
   [#71](https://github.com/nanorepublica/django-prodserver/issues/71)) so
   external packages can register backends without end-user setup.
2. Package-boundary cleanup that makes the core importable with only `django`
   installed (no `gunicorn`/`uvicorn`/etc. needed to import
   `django_prodserver`).
3. A federated test-suite layout so the per-adapter tests can later move with
   the adapter when a split happens.
4. Public docs of the plugin contract, plus a small example out-of-tree adapter
   that exercises it in CI.

It is intentionally **non-breaking**: today's `PRODUCTION_PROCESSES` dotted-path
backends and `pip install django-prodserver[gunicorn]` install command must keep
working unchanged.
