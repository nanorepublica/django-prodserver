# Specification: Split django-prodserver Into Multiple Repos/Packages

## Status

Exploratory spec. The goal of this spec is to **evaluate** structural options by
prototyping each on its own branch, then pick one. It is intentionally written as
parallel exploration tracks rather than a single linear implementation plan.

## Related Issues

- [#98](https://github.com/nanorepublica/django-prodserver/issues/98) —
  "Splitting out the backends and the core API". This is the parent issue this
  spec addresses: explore a future where the core API + commands can be merged
  into Django, with each backend ideally merged into its individual upstream
  project, and (as an immediate step) break the backends out into their own
  package(s). Raised by Jake at DjangoCon Europe.
- [#71](https://github.com/nanorepublica/django-prodserver/issues/71) —
  "Entrypoint support for backends". Directly satisfied by the shared
  prerequisite below; requested so external packages (e.g. Chancy) can register
  backends without end-user setup. Useful on its own even if the package is
  never split.

## Goal

Restructure django-prodserver so that:

1. A small, dependency-free **core** package can stand on its own and be a
   credible candidate for eventual inclusion in Django itself (via a DEP — Django
   Enhancement Proposal). The core owns the `server` / `devserver` / `prodserver`
   management commands, the `PRODUCTION_PROCESSES` setting, the `BaseServerBackend`
   / `BaseRunserverBackend` contract, and shared helpers.
2. Each third-party **backend adapter** (gunicorn, uvicorn, granian, waitress,
   werkzeug/runserver-plus, daphne, celery, django-tasks, django-q2) can live
   outside the core — ideally upstreamed into the server/worker project it wraps,
   or failing that in a dedicated satellite package — so users install only the
   adapters they actually run, and adapter releases track the upstream they
   depend on rather than the core's release cadence.

## Background & Motivation

The codebase already has a clean internal seam:

- **Core (no third-party deps):**
  - `src/django_prodserver/management/commands/server.py` (and the `prodserver`
    alias + `devserver`)
  - `src/django_prodserver/conf.py` (`AppSettings`, `PRODUCTION_PROCESSES`)
  - `src/django_prodserver/backends/base.py` (`BaseServerBackend`)
  - `src/django_prodserver/backends/_runserver_base.py` (`BaseRunserverBackend`)
  - `src/django_prodserver/backends/django_runserver.py` (wraps Django's own
    runserver — the only adapter with zero extra dependencies)
  - `src/django_prodserver/utils.py` (`wsgi_healthcheck`, `wsgi_app_name`,
    `asgi_app_name`)
  - `src/django_prodserver/apps.py`
- **Server adapters (one third-party dep each):** `gunicorn.py`, `uvicorn.py`,
  `granian.py`, `waitress.py`, `werkzeug.py` (379 lines — by far the largest),
  `daphne.py`.
- **Worker adapters (small, ≤72 lines):** `celery.py`, `django_tasks.py`,
  `django_q2.py`.

Backends are currently discovered by dotted path strings in
`PRODUCTION_PROCESSES["<name>"]["BACKEND"]` and the optional extras are declared
in `pyproject.toml` (`[project.optional-dependencies]`). Nothing in the runtime
actually depends on the adapters being in the same distribution — `import_string`
in `server.py:99` will happily import a backend class from any installed package.
That is what makes the split feasible.

See the **Related Issues** section above for the GitHub issues this spec
addresses (#98 is the driver; #71 is satisfied as a side-effect of the shared
prerequisite).

## Non-Goals / Out of Scope

- Actually submitting a Django DEP or merging anything into Django. This spec only
  makes the core *shaped like* a merge candidate.
- Actually opening PRs against gunicorn / uvicorn / django-tasks / django-q2 /
  celery. We will document which adapters are upstream-PR candidates and what the
  integration surface would be, but coordinating those merges is follow-up work.
- Changing the public configuration format in a breaking way. `PRODUCTION_PROCESSES`
  with dotted-path `BACKEND` strings must keep working unchanged.
- Renaming the management commands (tracked separately as #63 / #64).
- Adding new backends (Celery Flower #88, etc.).
- Publishing anything to PyPI as part of the spike — prototypes can be built and
  installed locally / from git, but actual releases are a separate decision.

## Phase 0 — Prerequisite (do this first, regardless of which split wins)

This was previously framed as "Option C" alongside A and B. It is **not** an
exploration track — it's a hard prerequisite that lands on its own branch and
merges to `main` before any of the split-option branches are started. The split
branches then fork from this work.

Phase 0 is independently valuable: even if no further split ever happens, it
delivers the entry-point contract requested in #71 (so external packages can
register backends) and makes the core's dependency surface explicit.

**Branch:** `claude/prodserver-entrypoint-foundation`

**Scope is non-breaking:**

- `PRODUCTION_PROCESSES["<name>"]["BACKEND"] = "django_prodserver.backends.gunicorn.GunicornServer"`
  keeps working.
- `pip install django-prodserver[gunicorn]` keeps working.
- All current tests stay green; no adapter modules move yet.

### P1. Entry-point–based backend discovery

- Define an `importlib.metadata` entry-point group, e.g.
  `django_prodserver.backends`. Each adapter package registers its backend
  classes there, e.g.:
  ```toml
  [project.entry-points."django_prodserver.backends"]
  gunicorn = "django_prodserver_gunicorn:GunicornServer"
  ```
- In the core, build a registry that:
  - Collects entry points lazily (on first `server` invocation).
  - Lets `PRODUCTION_PROCESSES[...]["BACKEND"]` accept **either** a registered
    short name **or** a dotted path (back-compat). Short name wins only if it
    resolves; otherwise fall back to `import_string`.
  - Surfaces a friendly error when a backend name maps to a package that isn't
    installed (e.g. "backend 'gunicorn' requires the `django-prodserver-gunicorn`
    package — `pip install django-prodserver-gunicorn`").
- Update `server --list` (and ideally a new `server --list-backends`) to show
  registered backends and whether their dependency is importable.

### P2. Package-boundary cleanup in the current tree

- Make `utils.py` import-safe without any optional dep (it already is — only
  imports Django).
- Confirm no core module imports an adapter module at import time (currently
  true; lock it in with a test).
- Ensure each adapter module's heavy import (`import gunicorn`, `import granian`,
  ...) happens inside `start_server` / `__init__`, not at module top level, so
  the registry can reference the class without the dep installed. (Audit each
  adapter; several already do this.)
- Decide the import name / distribution name convention for satellites:
  - Distribution: `django-prodserver-<name>` (e.g. `django-prodserver-gunicorn`).
  - Import package: `django_prodserver_<name>` **or** a PEP 420 namespace
    package `django_prodserver.contrib.<name>` — this choice is itself one of the
    things the option branches should test.

### P3. Test-suite federation plan

- The current `tests/backends/` suite exercises every adapter together. Decide
  how that splits: shared conformance test (a parametrized `BaseServerBackend`
  contract test) that lives in core and can be re-used by each satellite, plus
  adapter-specific tests that move with the adapter.
- Provide a `tox`/CI matrix story for "core only" vs "core + one adapter" vs
  "everything" so a contributor can run the slice they care about.

### P4. Document the plugin contract

- Add `docs/extending.md` (or equivalent) describing the entry-point group,
  what `BaseServerBackend` requires, and the satellite-package naming convention
  decided in P2.
- Add a tiny example out-of-tree adapter under `examples/` that registers itself
  via entry points and is exercised in CI as smoke proof that the contract works.

### Phase 0 done criteria

- Entry-point registry lands; both short names and dotted paths resolve.
- All existing tests green; no public-API breakage.
- Core import graph contains no third-party deps beyond `django`
  (assert this with a test).
- `docs/extending.md` published; example adapter installs and runs in CI.
- Branch is merged to `main`. All option branches below fork from it.

## Split Options To Explore (one branch each, after Phase 0)

Each option below should be prototyped far enough to answer the **decision
criteria** further down. Suggested branch names are given; the requester will
create/drive these branches.

Note: the *packaging strategy* (next section) is an orthogonal axis — every
option here should be tried under at least one packaging strategy, and ideally
its preferred one.

### Option A — Full multi-repo

**Branch:** `claude/split-multi-repo-spike`

- Core stays in this repo (possibly renamed to make the Django-merge intent
  obvious, e.g. `django-prodserver-core` distribution while keeping the
  `django_prodserver` import package).
- Each adapter (or logical group of adapters) moves to its own repo + PyPI
  package. Two sub-variants worth a quick look:
  - **A1:** one repo per adapter (`django-prodserver-gunicorn`,
    `django-prodserver-uvicorn`, ...). Maximal independence, maximal overhead.
  - **A2:** one `django-prodserver-contrib` repo holding all the adapters that
    *don't* get upstreamed, published either as one package with extras or as
    several packages from one repo.
- Adapters that are good upstream-PR candidates are documented as such
  (django-tasks, django-q2, celery, arguably gunicorn/uvicorn integrations) and
  the contrib repo carries them only until/unless upstream accepts them.
- Deliverables on the branch: a script or `git filter-repo` recipe showing how an
  adapter is extracted with history; a working `django-prodserver-gunicorn`
  prototype installed from a sibling directory; updated docs describing the new
  install story (`pip install django-prodserver django-prodserver-gunicorn`).

**Pros:** clean "lift core into Django" story; each upstream owns the code that
breaks when they release; users install only what they run.
**Cons:** N repos × release cadence × CI matrices is heavy for a small/solo
maintainer; cross-cutting `BaseServerBackend` changes need coordinated releases;
discoverability drops (no more single `pip install django-prodserver[gunicorn]`).

### Option B — Monorepo workspace of multiple publishable packages

**Branch:** `claude/split-monorepo-workspace-spike`

- Keep one repo, but restructure into a workspace (uv workspace or
  PDM/hatch equivalent) with several independently-publishable packages:
  ```
  packages/
    core/            -> django-prodserver-core   (the Django-merge candidate)
    gunicorn/        -> django-prodserver-gunicorn
    uvicorn/         -> django-prodserver-uvicorn
    granian/         -> django-prodserver-granian
    waitress/        -> django-prodserver-waitress
    werkzeug/        -> django-prodserver-werkzeug
    daphne/          -> django-prodserver-daphne
    celery/          -> django-prodserver-celery
    django-tasks/    -> django-prodserver-django-tasks
    django-q2/       -> django-prodserver-django-q2
    meta/            -> django-prodserver  (umbrella: depends on core + extras
                                            re-export the per-adapter packages)
  ```
- Shared CI, shared lint/format config, one place to make `BaseServerBackend`
  changes; each package still gets its own version + PyPI release + minimal
  dependency closure.
- The umbrella `django-prodserver` distribution keeps today's
  `pip install django-prodserver[gunicorn]` working by mapping extras to the
  per-adapter packages — no break for existing users.
- "Lift core into Django" = copy `packages/core/` — still clean, without the
  multi-repo tax.
- Deliverables on the branch: working uv workspace; `django-prodserver-core`
  builds with only `django` as a dep; at least two adapter packages build and
  install; CI runs the federated test matrix from P3; docs updated.

**Pros:** independent install/versioning + minimal deps per adapter, but one repo
to maintain; easiest migration path; can still flip individual packages out to
their own repos later (Option A) if an upstream bites.
**Cons:** workspace tooling complexity; publishing many packages from one tag
needs care (semantic-release config currently assumes one package); "merged into
respective upstream repos" still requires a later move.

> Option C from the previous draft ("single package, plugin-ready, no split") is
> not an option anymore — that work is **Phase 0** above and happens regardless.

## Packaging Strategy (orthogonal to Option A vs B)

The repo-layout decision (A vs B) is independent from the *install UX* decision.
The same code split can be shipped to PyPI in two distinct shapes, and the
trade-offs are different enough that each split option's branch should pick one
explicitly. These strategies are what determines what a user types when they
install.

### Strategy 1 — Umbrella extras preserved (recommended default)

The user-facing install command is **unchanged**:

```sh
pip install django-prodserver[gunicorn]
```

But under the hood:

- `django-prodserver` becomes a thin **umbrella distribution**. Its
  `[project.optional-dependencies]` map extras to the satellite adapter
  packages, not to the upstream server libraries directly:
  ```toml
  [project.optional-dependencies]
  gunicorn = ["django-prodserver-gunicorn"]
  uvicorn  = ["django-prodserver-uvicorn"]
  # ...
  ```
- `django-prodserver-gunicorn` is the satellite, and it depends on `gunicorn`
  itself. So the dependency chain resolves to
  `django-prodserver → django-prodserver-gunicorn → gunicorn`, plus
  `django-prodserver` pulling in `django-prodserver-core` (the actual core).
- Existing `PRODUCTION_PROCESSES` dotted paths still resolve, because each
  satellite ships a thin shim module at the old import path
  (`django_prodserver.backends.gunicorn`) re-exporting the moved class.

**Pros:** zero-friction migration; existing docs, blog posts, copilot
suggestions, deployment scripts keep working with no edits; users don't need to
know the split happened. This is the "same install experience, but installing
the adapter package instead of the raw server" shape.
**Cons:** more indirection in the dependency graph (one extra package per
adapter); umbrella publishing has to be coordinated with adapter publishing
(can't ship `django-prodserver 4.0` until the satellites it points at exist).

### Strategy 2 — Direct install per package

The user installs each piece explicitly:

```sh
pip install django-prodserver-core django-prodserver-gunicorn
```

`django-prodserver` (as a distribution name) is either retired, frozen, or kept
as a deprecated meta-shim that prints a warning.

**Pros:** cleanest dependency graph; easy to understand which adapter is in use;
mirrors how `pytest` + `pytest-django` (or `sqlalchemy` + `psycopg2`) is
typically installed.
**Cons:** breaks today's install instructions and `[extras]` syntax in every
existing deployment script and Dockerfile; requires a real deprecation period
and a migration note; bad first-run UX for users who copy old README snippets.

### Which strategy applies to which option

- **Option A (multi-repo):** can adopt **either** strategy. Strategy 1 needs the
  umbrella `django-prodserver` to live somewhere — likely this repo, now demoted
  to "umbrella + core" or split further to "umbrella" vs "core" repos.
- **Option B (monorepo workspace):** Strategy 1 is the natural fit (umbrella is
  just another package in the workspace). Strategy 2 is also possible by simply
  not publishing the umbrella package.

The recommended default for the first spike is **Strategy 1 + Option B**: same
install UX, no breaking change, split happens behind the extras. Strategy 2
becomes interesting later if/when adapters get upstreamed into their host
projects (e.g. gunicorn's repo starts shipping its own `django-prodserver`
adapter), because then the umbrella's gunicorn extra would point at *that*
upstream-owned package.

## Affected / Reference Files

Core (must remain dependency-free in every option):

- `src/django_prodserver/__init__.py`
- `src/django_prodserver/apps.py`
- `src/django_prodserver/conf.py`
- `src/django_prodserver/utils.py`
- `src/django_prodserver/backends/__init__.py`
- `src/django_prodserver/backends/base.py`
- `src/django_prodserver/backends/_runserver_base.py`
- `src/django_prodserver/backends/django_runserver.py` *(only zero-extra-dep adapter; candidate to ship with core)*
- `src/django_prodserver/management/__init__.py`
- `src/django_prodserver/management/commands/__init__.py`
- `src/django_prodserver/management/commands/server.py`
- `src/django_prodserver/management/commands/prodserver.py`
- `src/django_prodserver/management/commands/devserver.py`
- `src/django_prodserver/migrations/__init__.py`

Adapters to extract / make pluggable:

- `src/django_prodserver/backends/gunicorn.py`
- `src/django_prodserver/backends/uvicorn.py`
- `src/django_prodserver/backends/granian.py`
- `src/django_prodserver/backends/waitress.py`
- `src/django_prodserver/backends/werkzeug.py`
- `src/django_prodserver/backends/daphne.py`
- `src/django_prodserver/backends/celery.py`
- `src/django_prodserver/backends/django_tasks.py`
- `src/django_prodserver/backends/django_q2.py`

Packaging / tooling to touch:

- `pyproject.toml` (`[project.optional-dependencies]`, `[project.entry-points...]`,
  `[tool.semantic_release]` — currently single-package), `uv.lock`, `tox.ini`,
  `.github/` CI workflows, `docs/` (install + extending pages), `setup.py`.

Tests:

- `tests/backends/*` (federate per P3), `tests/test_server_command.py`,
  `tests/test_conf.py`, `tests/test_utils.py`.

## Decision Criteria (what each option branch must let us judge)

1. **Install ergonomics:** how many `pip install ...` lines does a typical user
   need, and is the error message good when an adapter dep is missing? Document
   under both packaging strategies.
2. **Maintainer overhead:** number of release pipelines, CI jobs, and changelogs;
   does `semantic-release` still work, or does it need replacing?
3. **Django-merge readiness:** can the core be built/tested/shipped with only
   `django` as a dependency, and is the public surface (commands + setting +
   `BaseServerBackend`) cleanly isolated?
4. **Upstream-PR viability:** for django-tasks, django-q2, celery — what exactly
   would a PR to those repos contain, and does the adapter need anything from the
   core beyond `BaseServerBackend`?
5. **Back-compat:** does an existing project with `PRODUCTION_PROCESSES` pointing
   at `django_prodserver.backends.gunicorn.GunicornServer` and
   `pip install django-prodserver[gunicorn]` keep working with no changes?
   (Strategy 1 should make this trivially yes; Strategy 2 should document the
   migration path.)
6. **Reversibility:** how hard is it to undo / re-merge if the experiment fails?

## Recommendation (to be confirmed after the spikes)

1. **Land Phase 0 first**, on its own branch and merged to `main`, before any
   split spike begins. This delivers #71 by itself and is independently shippable.
2. After Phase 0, prototype **Option B (monorepo workspace) + Strategy 1
   (umbrella extras)** as the primary candidate — it delivers per-adapter
   install/versioning + minimal deps + a clean "lift the core into Django" story
   *without* changing the user-facing install command.
3. Run a smaller spike for **Option A (multi-repo)** focused on the
   `git filter-repo` extraction recipe and what an upstream-PR-ready adapter
   looks like (e.g. a `django-prodserver-django-tasks` aimed at the django-tasks
   repo). Use this to validate that A is reachable from B on a per-adapter basis.
4. Treat **Option A** as the long-term end state for individual adapters that
   upstreams accept — not a big-bang migration.
5. **Strategy 2 (direct install)** is deferred: revisit once enough adapters
   live upstream that the umbrella stops adding value.

## Success Criteria

- **Phase 0** is merged to `main`: entry-point discovery + boundary cleanup +
  test federation + plugin-contract docs, with no breaking change to
  `PRODUCTION_PROCESSES` and all existing tests green.
- **Option-B branch** exists with a working uv workspace; `django-prodserver-core`
  builds with only `django` as a dep; at least two adapter packages
  (`gunicorn` + one worker) build and install via Strategy 1's umbrella extras;
  CI runs the federated test matrix from P3.
- **Option-A branch** exists with a documented `git filter-repo` extraction
  recipe and at least one extracted adapter working when installed from a
  sibling directory.
- Each branch has a short `FINDINGS.md` answering the six decision criteria.
- A written comparison (this spec updated, or a follow-up doc) names a winner
  and confirms the packaging strategy.
- Docs describe the chosen install story and the backend plugin contract.

## Risks & Mitigations

- **Release tooling:** `semantic_release` config in `pyproject.toml` assumes one
  package; multi-package publishing needs new config or a different tool.
  *Mitigation:* spike this explicitly on the Option B branch before committing.
- **Discoverability regression:** users currently find everything via one
  package + extras. *Mitigation:* default to **Packaging Strategy 1** (umbrella
  extras preserved) under whichever split option wins, so
  `pip install django-prodserver[gunicorn]` keeps working.
- **History loss on extraction:** *Mitigation:* use `git filter-repo` (document
  the recipe on the Option A branch) rather than fresh repos.
- **Upstreams say no:** gunicorn/uvicorn/celery may not want a Django-specific
  adapter. *Mitigation:* the contrib repo / per-adapter packages are the fallback
  home; nothing depends on upstream acceptance.
- **Namespace package pitfalls:** PEP 420 namespace packages (`django_prodserver.contrib.*`)
  can interact badly with some tooling. *Mitigation:* test both the namespace and
  the flat `django_prodserver_<name>` layouts on the option branches and pick the
  one that "just works".
