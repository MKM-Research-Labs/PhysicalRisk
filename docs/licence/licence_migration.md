# PhysicalRisk Licence Migration Plan

**Status:** draft — Phase 1 partially executed (see Progress)
**Owner:** MKM Research Labs
**Date:** 2026-07-17

---

## 1. Why

PhysicalRisk carries a restrictive non-commercial header on every source file:

> licensed by MKM Research Labs for non-commercial research and educational use
> only. Any commercial use, including ... internal business operations intended
> for commercial advantage, or research and development conducted for a
> commercial entity, is expressly prohibited unless separately authorized in
> writing.

Deploying into a bank's IT estate is *precisely* "internal business operations
intended for commercial advantage" and "research and development conducted for a
commercial entity" — the two things the header names as prohibited. **As written,
PhysicalRisk's own headers forbid the deployment being discussed.**

ModelRisk has already moved to MIT (see `LICENSE`, `copyright.py` in this
folder), and the deployment letter commits to five checkable facts:

1. MIT headers across the repository
2. A standard MIT `LICENSE` file at the repo root
3. A clean repository provided for handover
4. A dependency manifest with licences, containing "no unusual or restrictive licences"
5. No customer branding in the codebase

This plan makes each true for PhysicalRisk. MKM owns the copyright, so
relicensing is a decision, not a negotiation.

---

## 2. Current state (verified 2026-07-17)

| Item | State |
|---|---|
| Root `LICENSE` | **Added** — MIT, commit `2d30435a` |
| Canonical header source | `docs/shared/copyright.py` — swapped to MIT block (uncommitted) |
| File headers | **2,512 files still on the restrictive placeholder** |
| Customer branding | **None.** Only `_RATING_AGENCIES = ["S&P", "Moody's", "Fitch"]` — factual domain data |
| Data in repo | **None shipped.** `data/` is gitignored; 0 tracked files |
| Dependency licences | 23/25 BSD/MIT/Apache. **2 need a decision** (§5) |
| `.git` size | **465 MB** / 903 commits — see §4 |

### The mechanism that makes this cheap

`docs/shared/copyright.py` is the single source of truth. The audit
(`docs/models/full_audit/sections_tests/copyright_headers.py`) reads it
**verbatim** and `fix_repo(root, apply=True)` stamps it onto every `.py`/`.js`
file, self-healing under `app.py test`. Changing the licence is therefore *one
file edit plus one sweep* — the enforcement infrastructure is what makes the
switch nearly free.

---

## 3. Phase 1 — Licence migration

### 3.1 Progress

- [x] Add MIT `LICENSE` at repo root — `2d30435a`
- [x] Extract the MIT comment block into `docs/shared/copyright.py`
- [x] Update the test coupled to the old wording (`test_canonical_header_loads`
      asserted `'All rights reserved'`, which MIT drops)
- [x] Add guards: canonical must state MIT terms and must not say "non-commercial";
      canonical must have no trailing whitespace
- [ ] **Run the sweep** — `fix_repo(apply=True)`, 2,512 files
- [ ] Verify, commit, push

### 3.2 Gotchas found the hard way

**Take the comment block only, not the whole file.** `load_canonical_py` reads
the entire canonical file. ModelRisk's `copyright.py` has a docstring *after* the
comment block; copying it wholesale would stamp that docstring into all 2,512
files. Extract lines up to the first non-comment line.

**Keep `'all rights reserved'` in `_LICENSE_MARKERS`.** The markers identify an
*existing* header to replace. The check is `any()`, so MIT headers are still
matched via `'mkm research labs'` / `'copyright (c)'` — but removing the old
phrase would leave the sweep unable to recognise (and therefore replace) the
placeholder it is meant to remove.

**The trailing-whitespace war is fixed as a side effect.** The old canonical had
trailing spaces on 3 lines, which the self-heal propagated to every file, where
ruff's `W291` then flagged them — self-heal and linter fighting on every commit.
The MIT block is clean, so the sweep ends the conflict. A regression test now
pins it.

### 3.3 Sequencing

Do the licence swap **as** the sweep. A whitespace-only pass first would spend a
2,512-file commit on a header about to be deleted, and would leave the root
`LICENSE` (MIT) contradicting every file header until the second sweep. One
commit, one meaning.

---

## 4. Phase 2 — Repository history

### 4.1 What's actually in there

`.git` is **465 MB** across 903 commits. The cause is not source code:

| Blob | Size |
|---|---|
| `docs/models/test_results/test_history.json` | **38 MB current — 44 versions, 1,038 MB total** |
| `data/input/thames/storm_sequences.json` | 33 MB (data was tracked historically) |

`test_history.json` **is still tracked**, so every `app.py test` run rewrites it
and adds a fresh ~38 MB blob. The repository grows by ~38 MB per test run.

> **Prerequisite:** untrack (or cap/relocate) `test_history.json` *before* any
> history rewrite. Otherwise the bloat returns within days and the rewrite is
> wasted. This is arguably worth doing on its own merits regardless of the
> licence work.

### 4.2 Is a rewrite needed for the licence?

**No.** MKM holds the copyright and can relicense; the current `LICENSE` plus the
current headers govern what a recipient may do. Old commits containing the old
placeholder do not bind future use — the deployment letter says exactly this
("the earlier placeholder no longer applies"). History cleanup is therefore
about **repo hygiene and presentation**, not legal validity.

### 4.3 Options

| Option | Gets you | Costs |
|---|---|---|
| **A. Leave history alone** | Zero risk, zero effort | 465 MB clone; old headers visible in history |
| **B. Snapshot repo for handover** (recommended) | Clean MIT repo, no bloat, no old headers — dev history preserved internally | Two repos to reason about |
| **C. Rewrite in place** (`git filter-repo`) | One repo, small, clean history | Every SHA changes; invalidates all clones/worktrees; irreversible |
| **D. Fresh `git init`** (what ModelRisk did) | Simplest clean result | Loses all blame/bisect/provenance |

### 4.4 Recommendation — Option B

The letter's own approach for ModelRisk is a snapshot: *"we're providing a clean
repository initialised under the MIT licence, rather than the development repo
with its early iteration history."* That is Option B, and it does not require
touching MKM's development history at all.

Two reasons this matters more for PhysicalRisk than it did for ModelRisk:

- **The recipient doesn't want your history.** They clone, fork, and maintain
  internally. A snapshot is *better* for them — smaller and cleaner.
- **This is a model-governance platform.** Git history is part of its own
  provenance story: the Full Audit Report stamps a Git SHA on every page and
  claims figures reflect that commit. Destroying development history to publish a
  model-risk tool is an awkward look, and blame/bisect are worth real money on a
  codebase this size. Don't burn them to save 465 MB in a repo nobody else pulls.

**Practical shape:** keep `PhysicalRisk` as the development repo; publish
`PhysicalRisk-release` (or a tagged export) containing the MIT-headered tree with
a single initial commit. Regenerate the snapshot per release.

If Option C or D is chosen anyway: do it **after** Phase 1 (so the rewrite
carries MIT headers, not a mix), untrack `test_history.json` first, and expect to
re-clone every worktree — this repo currently has 10+, plus a detached-HEAD
checkout holding uncommitted work.

---

## 5. Phase 3 — Dependency manifest

The letter promises a manifest and asserts "no unusual or restrictive licences."
Verified against installed metadata — 23 of 25 are BSD/MIT/Apache. Two need a
decision:

| Package | Licence | Issue |
|---|---|---|
| `psycopg2-binary` | **LGPL with exceptions** | The only copyleft in the tree. The exception permits this use (linking without infecting), but LGPL is what automated scanners flag and what Legal will ask about. |
| `flask-cors` | **no metadata** | Ships no licence classifier at all; MIT upstream, but a generated manifest renders it "UNKNOWN" — which reads worse than LGPL. |

**Options for `psycopg2-binary`:** (a) keep it and state the exception plainly in
the manifest — accurate and defensible; (b) swap to `pg8000` (pure-Python, BSD)
and remove the conversation entirely. Recommend (a) unless Legal pushes back;
name it proactively rather than letting Cyber discover it.

**Suggested:** generate the manifest as a reproducible audit artefact (a §4.10
licence audit alongside the JSON and database-usage audits) rather than a
one-off spreadsheet — so the claim stays true on every run instead of decaying.

---

## 6. Verification

The claims must be *checkable*, since that is the point:

- [ ] `grep -ril "non-commercial" src/ app/ config/ tests/ docs/` returns nothing
- [ ] Every `.py`/`.js` begins with the MIT block (`fix_repo(apply=False)` reports
      `remaining == []`)
- [ ] Root `LICENSE` present and matches `copyright.py`'s body
- [ ] `ruff check src/ tests/` clean of `W291` in header lines
- [ ] Dependency manifest generated, every entry has a named licence
- [ ] Full unit suite green (the header audit is part of it)

---

## 7. Open decisions

1. **Does PhysicalRisk go MIT at all?** — *Decided 2026-07-17: yes, deliberately.*
   MKM is not a vendor and the platform is not where the IP sits. The platform is
   a **facilitator** — its job is to get banks and companies to participate. The
   commercial value is in becoming the **calculation service provider**, which is
   worth considerably more than licence revenue on the tooling. Open-sourcing the
   platform is distribution strategy, not a giveaway. See §7.5 for the boundary
   this implies.
2. **History:** Option B (snapshot) vs C/D (rewrite/fresh)?
3. **`psycopg2-binary`:** keep + disclose, or swap to `pg8000`?
4. **`test_history.json`:** untrack, cap, or move to the database?

5. **Where does the licence boundary fall — engine vs calibration?**

   If the business is the calculation *service*, the licence boundary should sit
   between the engine (ships, MIT — drives adoption) and the calibration (stays —
   it is the service). Verified state:

   | | Ships under MIT | Stays |
   |---|---|---|
   | Engine / algorithms | ✅ tracked | |
   | `config/` — **39 tracked files**, incl. `fire_matrices.json` (18K), `seismicmatrices.json` (7K), `seismic_zones.json` (4.6K) | ✅ tracked | |
   | `data/` — portfolios, gauges, classifiers, timeseries, hazard curves | | ✅ **0 tracked files** |

   The fuel does not travel — a recipient can run the platform but cannot *be* the
   calculation provider without the data, the calibration pipeline, and MKM. That
   supports the strategy.

   **But:** coding rule R1 ("every parameter lives in the `config` package")
   structurally routes *all* calibration into the tracked, MIT-licensed tree.
   Today that is largely harmless — the fire/seismic matrices are seed values, not
   real calibration. The issue is directional: as fire, seismic and wind are
   genuinely calibrated, those numbers land in `config/` **by construction** and
   ship **by default**. The rule that keeps the code clean also makes the
   calibration a distributable artefact.

   This is not an argument against MIT or against R1 — it is that the
   engine/calibration split the commercial model wants does not currently exist as
   a technical boundary. Decide while the values are still placeholders:

   - **`config/` is engine** → parameters are structure and defaults; ships; no change.
   - **`config/` is calibration** → R1 needs a carve-out: calibrated values live in
     `data/` or the database, `config/` holds shape and defaults only. Cheaper to
     draw this line now than to extract it later from 39 files under a licence
     that already permits redistribution.

---

## 8. Notes

- Not legal advice. The MIT-vs-commercial question and the LGPL exception both
  want a real review.
- The copyright year `2022-2026` in both `LICENSE` and `copyright.py` matches the
  existing PhysicalRisk header; no change needed.
