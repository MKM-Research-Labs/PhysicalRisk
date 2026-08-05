# Specification: Test Result Interpretation Agent

**Project:** PhysicalRisk
**Status:** Draft v0.3 — v0/v1 shipped; v2 (Documentation divergence) design added (§14)
**Author:** David
**Date:** 2026-08-05
**Reviewed:** 2026-08-05 (viability + repo grounding)

> **Review note (2026-08-05).** Changes below are marked inline with
> `> **Amended:**` / `> **Amendment:**` / `> **Answered:**` blockquotes. Two
> kinds: (a) factual reconciliation with the repo — the named audit tool does not
> exist under that name; pytest emits coverage XML but no JUnit XML; a known
> coverage-measurement bug on Python 3.13.1 threatens the Coverage section; output
> must not live under `data/`; and (b) a **design decision** taken in review —
> the runner is the **existing local nightly job**, and the agent runs as its
> final interpretation step (§3–§4 rewritten), with cloud-CI / per-PR execution
> deferred. None of this alters the agent's own contract (§6–§7).

---

## 1. Purpose

Automated test execution tells you *whether* something broke. It does not tell you
what the breakage means for the documented model, whether a coverage change matters,
or whether a passing change has quietly invalidated a stated model assumption.

This agent closes that gap. On each triggering event it reads the test outcome, the
diff, and the relevant model documentation, and emits a short written assessment for
human review.

The agent produces **documents, not actions**. It has no authority to commit, merge,
message, or modify source.

---

## 2. Scope

### In scope

- Interpreting test suite results in the context of the change that produced them
- Flagging coverage changes on modules whose responsibilities are documented
- Detecting divergence between code changes and documented model assumptions
- Producing a dated, versioned assessment artefact suitable for a validation file

### Out of scope (explicit non-goals)

- Running the test suite (CI does this — see §3)
- Fixing failing tests or modifying any source file
- Sending email, chat, or any outbound message
- Autonomous learning, self-modifying skills, or persistent cross-run state beyond
  the artefacts it writes
- Any judgement presented as authoritative — output is evidence for a reviewer,
  never a sign-off

---

## 3. Architecture

Two components. They are separate on purpose; only the second is an agent.

### 3.1 Runner (not an agent)

> **Amended (review 2026-08-05).** This section was rewritten from a cloud-CI
> runner to the **local nightly** model: the runner is the project's existing
> overnight job, and the agent runs as its final interpretation step. Cloud-CI /
> per-PR execution is retained as a deferred phase (§4).

The runner is the project's **existing overnight job**, not a cloud CI service. It
is deterministic, with no model involved: the nightly `app.py test … --audit` run
already executes the suite and the repository audit and leaves their output on disk.
The runner's only new responsibilities are to emit that output in machine-readable
form and, on completion, hand the agent a path.

Responsibilities:

1. Execute the test suite — the overnight run already does this, and already
   writes both `junit.xml` and `coverage.xml` into `config.get_reports_dir('audit')`
   (`full_audit` parses them from there). So the machine-readable test and coverage
   inputs **already exist locally**; the `--junitxml` gap is CI-only and belongs to
   the deferred cloud phase (§4), not v0.
2. Execute the repository audit — `python -m docs.models.full_audit` — in a
   structured (JSON) output mode. **This mode does not exist yet and is a v0
   prerequisite:** today the audit is a package emitting a sectioned *human*
   report the agent cannot parse reliably. There is no `split_audit.py`; that name
   in earlier drafts referred to this audit.
3. Ensure the four artefacts are at a known path:
   - test results (JUnit XML)
   - coverage report (XML + per-module summary)
   - audit tool output (JSON)
   - the diff for the change under assessment
4. On completion, invoke the agent with the path to those artefacts.

If the runner fails to produce any required artefact, the agent is **not** invoked
and the failure surfaces as an ordinary run failure. The agent never runs on partial
input.

### 3.2 Assessment agent

A bounded loop: read inputs, consult documentation, form an assessment, write one file,
stop. Terminates on completion or on iteration limit, whichever comes first.

---

## 4. Trigger

> **Amended (review 2026-08-05).** Reframed from PR/branch-push events to the
> **completion of the nightly run**. The original "explicitly not time-based" line
> is retired: the trigger is still an *event* (a run finished), it simply falls in
> the idle overnight window by construction.

**v0:** completion of the nightly run, plus manual invocation.

The interpretable event is **"the overnight suite finished."** The agent runs as
the final step of that job, in the idle overnight window while the machine is awake
but unattended (the same power / SSD-mounted / lid-awake prerequisites the overnight
suite already requires — it does **not** run while the machine is asleep). Because
the runner has just produced fresh test, coverage, audit, and diff artefacts, the
agent always has something real to interpret.

This is event-driven, not schedule-driven: the event is *run-completion*, and it
happens to occur at night because that is when the run occurs — not because of a
wall-clock cron. A fixed-time schedule independent of a run is explicitly avoided;
with nothing newly tested, there is nothing to interpret.

**Deferred to a later phase:** per-PR assessment in cloud CI (GitHub Actions,
`.github/workflows/ci.yml`), for faster feedback than a nightly cadence. That reuses
the same agent against CI-produced artefacts and changes only *where* the runner
lives and *how often* it fires — not the agent itself.

---

## 5. Inputs

| Input | Source | Required |
|---|---|---|
| Test results | Runner artefact | Yes |
| Coverage report (current) | Runner artefact | Yes |
| Coverage report (baseline) | Previous nightly run | No — degrade gracefully |
| Audit tool output | `full_audit` (JSON mode) | Yes |
| Change diff | VCS | Yes |
| Model documentation | Repository docs tree | Yes |
| Previous assessment | Last artefact written | No |

All paths resolved from a single configuration source (§8). No path literals anywhere
in the implementation.

---

## 6. Tool surface

Deny by default. The agent is granted exactly these capabilities:

- **Read** — files under the repository root and the runner artefact directory
- **Write** — a single file, at the configured output path, and nowhere else

No shell execution. No network access. No write access to source, tests, configuration,
or documentation.

Rationale: the value of this agent is that its output can be trusted as an input to
model validation. That property is destroyed the moment it can alter the thing it is
assessing.

---

## 7. Output

Markdown is the source-of-truth body; the **delivered artefact is a PDF** rendered
from it, one per run.

> **Amended (review 2026-08-05) — delivery via the audit workflow.** The assessment
> is rendered to a **standalone sibling PDF** and written to
> `config.get_reports_dir('audit')` (→ `data/output/audit/`) — the same directory
> `full_audit` writes `full_audit_report.pdf` to, using the same reportlab
> `styles.py` / `helpers.py`. The Model Governance panel's Audit Reports section
> already lists **every** file in that directory (`/governance/audit-reports` in
> `src/routes/governance/audit_reports.py`, rendered by
> `src/static/js/mg-audit-reports.js`) and serves each via a `/file/<name>`
> download route — so the PDF **surfaces on the audit workflow with no extra
> wiring**. Filename follows the dated pattern below
> (`assessment_{ISO-date}_{short-sha}.pdf`). The markdown may be retained beside it
> as the reviewable/diffable source.

### Required structure

```
# Assessment: <short-sha>

**Date:** <ISO 8601>
**Commit:** <full sha>
**Branch:** <branch>
**Test outcome:** PASS | FAIL | ERROR
**Reviewer attention required:** YES | NO

## Summary
<Two to four sentences, plain English. What changed and what it means.>

## Test outcome
<Failures listed individually. For each: the test, the assertion, and an
assessment of whether it indicates a regression in behaviour or a change in
expectation. Where the agent cannot tell, it says so.>

## Coverage
<Only modules whose coverage changed. Change stated with its magnitude and
the documented responsibility of the module. Silence where nothing moved.>

## Audit findings
<New violations from the `full_audit` run, and violations resolved.>

## Documentation divergence
<Changes touching behaviour described in model documentation, with the
specific document and section. This section is the primary deliverable —
it is the one no test runner can produce.>

## Uncertainties
<Anything the agent could not determine, stated explicitly rather than
omitted. A short list here is expected on most runs.>
```

> **Amendment (Coverage — measurement-artefact risk).** On **Python 3.13.1** this
> project's coverage under-reports (~84% measured vs ~99.3% true) because of a
> `sys.monitoring` tracer defect; CI pins 3.13 and the mitigation is
> `core=ctrace` in `pyproject`. Since the Coverage section interprets *deltas*
> against a baseline, a tracer difference between baseline and current runs can
> present as a large, entirely spurious coverage regression — exactly the
> fabricated finding §9 forbids. **Controls:** (a) pin the coverage core
> explicitly for the runner so baseline and current are measured identically;
> (b) instruct the agent to treat any coverage swing not localised to files in
> the diff as an environment signal for **Uncertainties**, never as a finding.

### Output constraints

- Sections with nothing to report are rendered as a single line, not padded
- No section is omitted — absence of a heading is indistinguishable from failure
- The agent never states a conclusion it cannot ground in a supplied input
- Where evidence is insufficient, that goes under **Uncertainties**, not into the body
  as hedged prose

---

## 8. Configuration

Single configuration module. Every path, threshold, model identifier, and iteration
limit is defined once and imported. No literals in the agent implementation.

Configurable at minimum:

- Artefact input directory
- Output directory and filename pattern
- Documentation tree root
- Coverage change threshold below which a module is not reported
- Maximum agent iterations
- Maximum token spend per run
- Model identifier

> **Amended (review 2026-08-05) — output location corrected.** An earlier draft
> said output must not be under `data/`. That was too broad. The correct sink is
> `config.get_reports_dir('audit')` → **`data/output/audit/`**, which is
> regenerable **output** and is exactly what the audit workflow reads (§7). The
> "do not mutate `data/`" rule protects `data/input` (port/property data on the
> shared SSD) and governance *source* data — **not** `data/output`, which tooling
> writes to routinely (`coverage.xml`, `full_audit_report.pdf` already live
> there). Because that tree is not committed, there is no per-run commit churn.
> Resolve the path from config (§8), never as a literal.
>
> The coverage core setting (§7 amendment) is also configured here, so baseline
> and current runs are guaranteed to use the same tracer.

---

## 9. Guardrails

| Risk | Control |
|---|---|
| Runaway loop | Hard iteration cap; process exits non-zero on cap |
| Cost overrun | Per-run token ceiling; run aborts and writes a stub artefact on breach |
| Silent degradation | Every run writes an artefact, including on agent failure |
| Fabricated findings | Agent is instructed to ground every claim in a named input; ungrounded claims are a defect |
| Scope creep into action-taking | Tool surface is deny-by-default (§6); adding a write path is a spec change, not an implementation detail |

---

## 10. Testing requirements

The agent is itself subject to the project's coverage requirements. Deterministic
components are unit tested conventionally. The model-dependent step is tested against
a fixture corpus:

- A set of committed input fixtures (diff + results + docs) with known correct
  characterisations
- Assertions on **structure and grounding**, not on exact prose: every required
  section present, every factual claim traceable to a fixture input, no claim about a
  file not in the diff
- A fixture where the correct answer is "insufficient information," asserting the
  agent populates **Uncertainties** rather than guessing

---

## 11. Phasing

**v0 — Deterministic spine**
CI runs tests and `split_audit.py`, emits artefacts, writes a templated summary with
no model involved. Establishes the pipeline and proves the artefacts are well-formed.

**v1 — Interpretation**
Agent reads v0 artefacts plus the diff. Produces Summary, Test outcome, Coverage,
Audit findings, Uncertainties. Documentation divergence deferred.

**v2 — Documentation divergence** — detailed design in **§14**.
Agent gains read access to the documentation tree and produces the divergence section.
This is the section with the most value and the most room to be wrong, so it ships last
and against the largest fixture set. Locked posture: high-precision detection,
adversarial verification, targeted+capable model (§14.1).

**v3 — Data lineage**
Lineage trail for inputs feeding changed modules. Requires lineage metadata that does
not exist yet; out of scope until it does.

---

## 12. Open questions

To be resolved before implementation begins.

1. **Test framework and runner.** Assumed pytest with coverage. Confirm, and confirm
   what CI is available — GitHub Actions, or something local?
   > **Answered.** pytest + coverage on GitHub Actions (`.github/workflows/ci.yml`):
   > jobs `lint` (ruff), `test` (coverage→`coverage.xml`), `test-pg` (Postgres
   > parity). Coverage XML already emitted; JUnit XML is not (see §3.1 amendment).
2. **Documentation location and format.** Where does the model documentation live
   relative to the repository, and is it structured enough to reference by section?
   > **Answered — favourable.** Model docs live in `docs/models/<model>/` as
   > structured LaTeX (`\section`s). Better still, `model_inventory.json` carries
   > `source_module` links mapping code modules → model docs (the chain
   > `full_audit §4.7` validates), giving v2 a ready-made code→doc lookup instead
   > of an inference. This is the biggest de-risker for the divergence section.
3. **Baseline for coverage comparison.** Is there a stored baseline, or does the agent
   compute one from the previous run?
   > **Open, with a caveat.** No stored baseline today; compute from the previous
   > `main` run. Whichever source is chosen, it must be measured with the same
   > coverage core as the current run (see §7 / §8 amendments) or the delta is
   > meaningless.
4. **Artefact retention.** Do assessments live in the repository, or in a separate
   store? Repository is simpler and gives free version history, but adds a commit per
   run unless written to an ignored path.
   > **Constrained.** Must not be under `data/` (shared SSD symlink). Prefer a
   > git-ignored path or a dedicated `assessments/` branch — see §8 amendment.
5. **Model selection and cost tolerance.** What per-run spend is acceptable, and does
   that change the phasing?
   > **Still open — for David.** Genuinely a business/cost decision; no repo answer.
6. **Repo vs. MKM-ModelRisk (new).** A test-interpretation agent that reads model
   docs + coverage is a *model-governance* capability, and governance is being
   extracted into a separate **MKM-ModelRisk** repo. Decide deliberately whether
   this ships inside PhysicalRisk or as an MKM-ModelRisk tool consuming
   PhysicalRisk as its first corpus — it determines where the config module and
   documentation-tree root point.

---

## 13. Acceptance

v1 is accepted when, on a corpus of at least ten historical commits from PhysicalRisk,
the agent produces a well-formed artefact for every one, and a reviewer judges the
Summary section accurate on each. Accuracy here means: nothing asserted that is untrue,
and nothing material to the change omitted. Elegance of prose is not a criterion.

---

## 14. v2 design — Documentation divergence

This section details v2 (the §11 stub). It is the first section that runs a model
and the first that can be wrong, so its design is dominated by *not fabricating*.
Everything v0/v1 does stays deterministic; v2 adds a bounded model step whose every
claim is anchored to a verbatim quote from a supplied input.

### 14.1 Decisions (locked, review 2026-08-05)

| Axis | Decision | Consequence |
|---|---|---|
| Detection posture | **High-precision** | Flag only a change that contradicts a *specific, quotable* documented claim. A missed subtle divergence is safer than a false alarm that erodes trust in the artefact. |
| Verification | **Adversarial second pass** | Every candidate is independently re-judged by a model prompted to *refute* it; it survives only if the refutation fails. ~2× model cost, sharply lower fabrication. |
| Model & cost | **Targeted + capable** | A capable model (Opus/Sonnet tier), fed only the mapped doc section(s) + the specific diff hunk — never whole documents. Keeps per-run tokens bounded under the §9 ceiling. |

### 14.2 The code→doc bridge (deterministic)

Grounded in what the repo already has:

- `docs/models/governance_data/model_inventory.json` — each model carries
  `model_id` ↔ `source_module` (e.g. `MKM-SI-001` ↔ `src/models/intensity/distribution.py`).
- a model_id → `docs/models/<slug>/` registry (the one the test-results generator
  already uses) locates the LaTeX docs; the primary doc is `<slug>.tex`, structured
  by `\section`/`\subsection`.

**Matching rule.** A changed file `F` in the diff maps to model `M` when `F` equals
`M.source_module` **or** sits under that module's package directory. `source_module`
often names a file that has since become a package (the <300-line split rule), so
matching is **prefix-aware**, and a mismatch (source_module no longer on disk) is
itself surfaced under Uncertainties rather than silently dropped.

Changed files that map to **no** documented model (the PLATFORM majority) are
**skipped, and the skip is stated** in the section (no silent truncation).

### 14.3 Pipeline (per affected model)

Deterministic stages are plain code; model stages are the only non-deterministic part.

0. **Affected-model set** (deterministic) — from the diff, apply the bridge. Empty
   set → the section renders one line: *"No change touched a documented model."*
1. **Extract** (deterministic) — for each affected model gather (a) its diff hunks and
   (b) *targeted* doc excerpts: parse `<slug>.tex` into sections, select those whose
   text references the changed symbols (function/class names from the diff), falling
   back to the methodology/assumptions sections. Bounded by a per-model token budget
   (§8); what was truncated is recorded.
2. **Detect — model pass 1** (high-precision) — the model receives the diff hunks +
   the doc excerpts and returns candidate divergences, each **required** to quote (i)
   the exact doc sentence and (ii) the exact diff line it contradicts, with a one-line
   why. "Nothing contradicts" is a valid, expected answer.
3. **Verify — model pass 2** (adversarial) — each candidate goes to an independent
   pass instructed to *argue it is not a real divergence, defaulting to refuted when
   uncertain*. A candidate is kept only if the refutation fails.
4. **Render** — survivors populate **Documentation divergence**, each citing model,
   doc, `\section`, the quoted sentence and the diff line. Anything the model was
   unsure of, or could not ground, goes to **Uncertainties** — never into the body as
   hedged prose.

### 14.4 Grounding rules (anti-fabrication — the core of v2)

- Every divergence **must** quote a verbatim doc sentence **and** a verbatim diff
  line. A finding missing either quote is a **defect**, rejected by a deterministic
  post-validator before render (not left to the model's goodwill).
- No finding may reference a file absent from the diff, or a doc section not supplied
  to the model.
- The body states only survived-adversarial-verify findings. Confidence is not prose;
  it is "survived / did not."

### 14.5 Tool surface & config (extends §6, §8)

- Read-only still holds; docs are already readable under §6. The **one** new
  capability is reaching the model endpoint — the sole, explicit exception to §6's
  no-network rule, scoped to that endpoint only. (A locally-hosted model needs no
  exception; see §14.8.)
- New config (§8): per-model and per-run token ceilings, max doc-section tokens, max
  models assessed per run, and the `model_inventory` + doc-registry paths. All from
  the config package, no literals.

### 14.6 Guardrails (extends §9)

| Risk | Control |
|---|---|
| Fabricated divergence | High-precision prompt + adversarial verify + deterministic quote-validator; a finding without both verbatim quotes never renders |
| Cost overrun on a large diff | Per-run token ceiling; when hit, the run stops assessing further models and **names the models it did not reach** (no silent cap) |
| Non-determinism | The section is evidence, not a verdict; re-runs may differ. Stated in the section and in Uncertainties |
| Missing the bridge | A `source_module` not found on disk → Uncertainties, plus a nudge that `model_inventory.json` needs updating |

### 14.7 Testing (extends §10)

Deterministic parts (bridge/matching, section selection, quote-validator) are
unit-tested to ≥99%. The model step is tested against a committed fixture corpus of
`(diff, doc-excerpt)` pairs with known labels, asserting **structure and grounding,
not prose**:

- **true-divergence** fixtures — a change that contradicts a documented claim →
  assert a grounded finding quoting the right sentence.
- **no-divergence** fixtures — a change to a documented model that stays consistent →
  assert **no** finding survives.
- **insufficient-info** fixture — assert **Uncertainties**, not a guess.
- **unmapped-change** fixture (PLATFORM code) — assert skipped **and** stated.

Because the model is non-deterministic, the CI assertion is the quote-validator
(every finding quotes a supplied sentence + a diff line; none references unsupplied
files); a separate, flaky-tolerant calibration run over the labelled set tracks
precision/recall but does not gate CI.

### 14.8 Open questions (v2)

1. **Model access from the local-nightly runner.** The overnight job would need egress
   to the model endpoint (API key handling, or a locally-hosted model with no egress).
   Which, and how is the key supplied to a non-interactive run? Ties to §12.5/§12.6.
2. **Section-selection heuristic.** Start simple — `\section`-title + changed-symbol
   keyword match — and only add retrieval/embeddings if recall proves too low.
3. **Pre-existing vs. introduced divergence.** v2 flags divergence *introduced by this
   diff*. Standing drift unrelated to the change is arguably a separate "documentation
   consistency" audit; confirm it is out of v2 scope.
4. **`source_module` drift.** Files split into packages leave `source_module` pointing
   at a vanished path. Decide: keep `model_inventory.json` current as policy, or make
   matching fully prefix-aware and tolerant.

### 14.9 Internal phasing

- **v2a** — bridge + section selection + detection pass only, single-pass, behind a
  flag, writing to a scratch area for calibration (not the live section).
- **v2b** — add the adversarial verify + the quote-validator, then promote to the live
  **Documentation divergence** section.
