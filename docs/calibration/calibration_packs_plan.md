# Calibration Packs — Project Plan

**Status:** draft for review
**Owner:** MKM Research Labs
**Date:** 2026-07-17
**Related:** [`docs/licence/licence_migration.md`](../licence/licence_migration.md) §7.5

---

## 1. Objective

The platform is a **facilitator** — MIT-licensed, given away to get banks and
companies to participate. The commercial value is in being the **calculation
service provider**. Calibration is therefore not a config detail; it is *the
product*.

Two tiers:

| Tier | Ships | Purpose |
|---|---|---|
| **Generic** | Yes — in the MIT repo | Credible out-of-the-box results. Must be good enough that the platform is genuinely useful, or nobody adopts it. |
| **Bespoke** | No — delivered | Client-specific, materially more accurate, governed. The revenue line. |

### The legal linchpin

MIT covers **software**. A calibration pack is **data**, and data is licensed
separately under whatever commercial terms MKM chooses. This is the same split
as an open-source database engine versus the data in it.

That split only holds while packs are **outside the repository**. Any bespoke
pack committed to the MIT tree is MIT-licensed forever, irrevocably. This is the
single most important constraint in this document.

---

## 2. Current state (verified 2026-07-17)

### The good news — the pattern already exists

The two newest models already do exactly what this project needs:

- `config/seismic/_loader.py`: *"No numeric value is embedded in code; everything
  is read from `config/seismicmatrices.json` and `config/seismic_zones.json`."*
  Signature: `load_seismic_config(matrices_path=DEFAULT_MATRICES_PATH, zones_path=DEFAULT_ZONES_PATH)`
  — **the override seam is already there.**
- `config/fire.py`: *"the module never embeds the numbers; it only describes their
  structure and loads."*

So **fire and seismic are already schema-in-code + numbers-in-data + loader**.
This project generalises that pattern rather than inventing one.

### The backlog

| | Count |
|---|---|
| `config/` modules with module-level literal constants | **16** |
| Module-level constants total | **206** |
| Of which infrastructure (not calibration) — `data_layout` (35), `visual` (10), `auth` (6) | ~51 |
| **Calibration to migrate** | **~155** |

Largest calibration-bearing modules:

```
26  config/port/_storm.py         19  config/models/_flood.py
19  config/models/_valuation.py   18  config/port/_book.py
17  config/bri.py                 16  config/port/_misc.py
12  config/damage.py              11  config/loan.py
```

`config/damage.py` is the archetype — and shows exactly what is at stake:

```python
# Control points for the piecewise-linear depth-damage curve.
# Calibrated to UK residential flood loss data.        <-- (UK-calibrated, JBA / MCM lineage)
DEPTH_POINTS:  List[float] = [0, 0.05, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
DAMAGE_POINTS: List[float] = [0, 0.05, 0.25, 0.40, 0.50, 0.60, 0.75, 0.85, 0.95, 1.0]
```

Real calibration with real lineage, as import-time module constants, in a tree
about to be MIT-licensed.

### What already doesn't ship

`data/` has **0 tracked files** — portfolios, gauges, classifiers, timeseries and
hazard curves never travel. The fuel is already outside the boundary. The gap is
`config/` (39 tracked files), which sits on the shipping side.

---

## 3. The real blocker (and the honest cost)

This is **not** a data-move. It is a **call-site migration**.

```python
from config.damage import DEPTH_POINTS      # binds at import, process-wide
```

Import-time constants cannot be swapped per run, per tenant, or per calibration
version. Every consumer must move from importing a value to *asking* for one:

```python
from calibration import depth_damage_curve
curve = depth_damage_curve()                # resolved against the active pack
```

That is the same shape as the `src/database` seam migration — and it took real
effort. Expect the same here: the pack format is a week; the call sites are the
project. Scope it accordingly.

---

## 4. Target architecture

### 4.1 The seam

A single `src/calibration/` package, mirroring `src/database/` — one public API,
no calibration access anywhere else, enforced by an audit (§8). This deliberately
reuses a pattern already proven in this codebase.

### 4.2 What lives where

| Layer | Contents | Licence | Ships |
|---|---|---|---|
| `config/` | **Schema only** — shape, types, units, validation, defaults-as-structure | MIT | ✅ |
| Generic pack | The free numbers | MIT (or open data terms) | ✅ |
| Bespoke pack | Client-specific numbers | Commercial | ❌ |
| `src/calibration/` | Loader, resolution, provenance | MIT | ✅ |

### 4.3 Pack

A pack is an **immutable, addressable, versioned** set of numbers plus metadata:

```
pack_id      mkm/uk-generic          |  client-x/thames-2026H1
version      1.4.0                   |  2026.07.1
scope        peril, geography, asset class
provenance   source data, method, date, author, approver
valid_from   / valid_to
checksum     content hash
```

Immutability is not optional — reproducing a 2026 number in 2029 requires the
exact pack that produced it.

### 4.4 Resolution order

```
bespoke pack (if present and entitled)
  └─> generic pack (ships)
        └─> HARD FAIL — never a silent default
```

**Silent fallback is a governance hole**, not a convenience: a result computed on
generic numbers but attributed to a bespoke calibration is a mis-stated model
output. Fail loudly, and record which pack actually resolved. (Compare the
Postgres preflight added 2026-07-17: a missing service must announce itself, not
degrade quietly into a wrong-looking number.)

### 4.5 Delivery

Reuse what exists — do not build new infrastructure:

- **`src/database` seam + Postgres** — pack registry, versions, entitlement
- **MinIO blob tier** — pack payloads (already used for classifiers/particles)

Both are built, tested and already in the deployment story.

---

## 5. Governance — the differentiator

For a model-risk platform this is the part that makes bespoke calibration worth
paying for. A model output is a function of:

```
result = f(code version, input data, CALIBRATION VERSION)
```

The third term is currently unrecorded anywhere.

Required:

- **Lineage manifest** records `pack_id` + `version` per step (it already records
  generator + parameters — this is an extension, not a new mechanism)
- **Model inventory** references the calibration each model is running
- **Audit report** states which pack produced the numbers
- **Reproducibility**: given a run, recover the exact pack

A regulator *will* ask "which calibration produced this number, and who approved
it?" Being able to answer in one click is a selling point, not overhead. It is
also the natural moat: the numbers can be copied; the governed, versioned,
approved, reproducible **provenance trail** is the service.

---

## 6. Phases

| Phase | Work | Output |
|---|---|---|
| **0. Classify** | Triage all 206 constants → calibration \| infrastructure \| structure. Cheap, and it defines everything downstream. | Registry: constant → class → owner |
| **1. Seam + generic pack** | Stand up `src/calibration/`. Generalise the fire/seismic loader. Extract `damage.py` first — smallest real calibration, clearest lineage, one consumer. | Working seam, one model migrated |
| **2. Call-site migration** | Module by module: constants → accessors. `bri`, `loan`, `models/_flood`, `models/_valuation`, `port/_storm`, `port/_book`. **The bulk of the work.** | `config/` holds schema only |
| **3. Bespoke packs** | Pack format, registry, versioning, resolution, entitlement, delivery via DB/MinIO. | Two-tier calibration works |
| **4. Provenance** | Lineage + inventory + audit record pack id/version. | Reproducible, governed results |
| **5. Commercial** | Backtest generic vs bespoke to *quantify* the delta — the sales artefact. Packaging, pricing, update cadence. | Demonstrable value |
| **6. Enforce** | Audit section: no calibration literal outside a pack. Zero-tolerance, like the JSON and database-usage audits. | Cannot regress |

**Sequencing note:** Phases 0–2 are worth doing on their own merits — they are
also what the licence boundary needs. Phase 3 onward is the revenue mechanism.
Do 0 and 1 before the calibration values become real, or you will be extracting
them later from a tree that is already MIT.

---

## 7. Rule R1 carve-out

Current coding rule R1: *every parameter lives in the config package.*

That rule is why calibration is structurally on the shipping side — it routes all
numbers into `config/` **by construction**. It needs amending, not abandoning:

> **R1 (revised):** every parameter's *schema* lives in the `config` package.
> Calibrated *values* live in a calibration pack, reached through the
> `src/calibration` seam. No calibrated literal appears in `config/` or in model
> code.

Two existing audits will fight this and must be taught the distinction:

- **Hard-coding audit** — currently flags ALL_CAPS constants *outside* `config.py`
  as violations. Under the new rule, calibrated constants *inside* `config/` are
  the violation.
- **Path audit** — pack locations must be registered in the config path registry.

---

## 8. Open decisions

1. **Pack granularity** — per model, per peril, per geography, per client, or a
   composed stack (client overlay on top of a generic base)? A composed stack is
   more flexible and much harder to reason about in an audit.
2. **Delivery** — DB rows, MinIO blobs, or signed files? (DB + MinIO already exist.)
3. **Entitlement** — MIT code cannot enforce anything. The *pack* is the gate: no
   pack, no bespoke numbers. Is that sufficient, or is a signature/licence check
   needed? Note any enforcement code shipped under MIT can simply be deleted by
   the recipient.
4. **Generic-pack quality** — must be usable enough to drive adoption, generic
   enough that bespoke is worth buying. This is a product judgement, and the whole
   two-tier model turns on getting it right.
5. **Fallback policy** — confirm hard-fail. Recommended: no pack, no number.
6. **Who approves a pack?** — bespoke calibration entering a bank's model estate
   will need a named approver and an MRC-style sign-off. Design it in from Phase 3.

---

## 9. Risks

- **Call-site breadth** — the migration touches every model consumer. Underscoping
  this is the main delivery risk.
- **Silent fallback** — results attributed to the wrong calibration. Governance
  hole; hard-fail from day one.
- **Irreversibility** — a bespoke pack committed to the MIT tree is MIT forever.
  Gate this in CI (§6 Phase 6) before Phase 3 ships anything real.
- **Audit conflict** — the hard-coding audit enforces the *old* rule. It will go
  red the moment calibration leaves `config/`. Sequence the audit change with the
  code change.
- **Generic too good / too poor** — no revenue, or no adoption.

---

## 10. Notes

- Not legal advice. The code/data licence split is standard practice, but the
  pack terms want a real review.
- The fire and seismic loaders are the reference implementation. Start there
  rather than designing from scratch.
