# `catch/` — catchment parameters

Version-controlled home for catchment parameter modules. See the docstring in
`__init__.py` for why they live here rather than under `data/catch/`.

**Currently empty.** The parameters are on the external data volume and cannot
be copied while it is detached. Until a catchment is vendored here, it resolves
from `data/catch/` as before — the two locations coexist and the repo one wins.

Migration is per-catchment and reversible: copy the module (or directory) in,
run `python -c "import catch.<id> as m; print(m.__file__)"` to confirm the repo
copy is the one being imported, then delete the copy under `data/catch/` only
once a full generation run has passed against it.

What belongs here — all generation *inputs*:

- `<id>.py` or `<id>/` — `BOUNDS`, `CURRENCY`, flood thresholds, gauge seeds
- `<id>/tc.py` — tropical-cyclone exposure (opt-in per catchment)
- `<id>/fault_trace.json` — seismic source-to-site geometry
- BRI prototype workbooks used for building-code sampling

What does not: anything a `port` run produces. That is data, and it belongs
under the data root.
