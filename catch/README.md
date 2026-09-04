# `catch/` — catchment parameters

Version-controlled home for catchment parameter modules. See the docstring in
`__init__.py` for why they live here rather than under `data/catch/`.

**Vendored so far: `thames`.** Anything not vendored still resolves from
`data/catch/` — the two locations coexist and the repo one wins.

Migration is per-catchment and reversible. A directory-form catchment imports
the shared `base` module as a sibling (`from ..base import BaseCatchment`), so
copying the directory alone leaves it unimportable:

    SRC="$(python -c 'from config import config; print(config.data_root)')/catch"
    cp "$SRC/base.py" catch/          # shared, needed once
    cp -R "$SRC/thames" catch/        # or: cp "$SRC/thames.py" catch/

Then confirm the repo copy is the one being imported:

    python -c "import catch.thames as m; print(m.__file__)"

Delete the copy under `data/catch/` only once a full generation run has passed
against the vendored one.

Note the shadowing is all-or-nothing: as soon as `catch/` holds one catchment
it wins for *every* lookup, so a catchment vendored incompletely takes
precedence over the working copy on the volume and breaks it. Import-check
each one after copying.

What belongs here — all generation *inputs*:

- `<id>.py` or `<id>/` — `BOUNDS`, `CURRENCY`, flood thresholds, gauge seeds
- `<id>/tc.py` — tropical-cyclone exposure (opt-in per catchment)
- `<id>/fault_trace.json` — seismic source-to-site geometry
- BRI prototype workbooks used for building-code sampling

What does not: anything a `port` run produces. That is data, and it belongs
under the data root.
