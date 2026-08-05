# Specification: Test Result Interpretation Agent

**Project:** PhysicalRisk
**Status:** Draft v0.1 — for review before implementation
**Author:** David
**Date:** 2026-08-05

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

Standard CI. Deterministic, no model involved.

Responsibilities:

1. Execute the test suite on the trigger event
2. Execute `split_audit.py`
3. Emit machine-readable artefacts to a known path:
   - test results (JUnit XML or equivalent)
   - coverage report (XML + per-module summary)
   - audit tool output
   - the diff for the triggering change
4. Invoke the agent with the path to those artefacts

If the runner fails to produce any required artefact, the agent is **not** invoked and
the failure surfaces as an ordinary CI failure. The agent never runs on partial input.

### 3.2 Assessment agent

A bounded loop: read inputs, consult documentation, form an assessment, write one file,
stop. Terminates on completion or on iteration limit, whichever comes first.

---

## 4. Trigger

**v0:** manual invocation and on push to any branch.

**Later:** on pull request open and update.

Explicitly **not** time-based. Nothing about this work benefits from running on a
schedule, and cron triggers create cost with no corresponding event to interpret.

---

## 5. Inputs

| Input | Source | Required |
|---|---|---|
| Test results | Runner artefact | Yes |
| Coverage report (current) | Runner artefact | Yes |
| Coverage report (baseline) | Previous run on main | No — degrade gracefully |
| Audit tool output | `split_audit.py` | Yes |
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

One markdown file per run, at `{output_dir}/{ISO-date}-{short-sha}.md`.

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
<New violations from split_audit.py, and violations resolved.>

## Documentation divergence
<Changes touching behaviour described in model documentation, with the
specific document and section. This section is the primary deliverable —
it is the one no test runner can produce.>

## Uncertainties
<Anything the agent could not determine, stated explicitly rather than
omitted. A short list here is expected on most runs.>
```

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

**v2 — Documentation divergence**
Agent gains read access to the documentation tree and produces the divergence section.
This is the section with the most value and the most room to be wrong, so it ships last
and against the largest fixture set.

**v3 — Data lineage**
Lineage trail for inputs feeding changed modules. Requires lineage metadata that does
not exist yet; out of scope until it does.

---

## 12. Open questions

To be resolved before implementation begins.

1. **Test framework and runner.** Assumed pytest with coverage. Confirm, and confirm
   what CI is available — GitHub Actions, or something local?
2. **Documentation location and format.** Where does the model documentation live
   relative to the repository, and is it structured enough to reference by section?
3. **Baseline for coverage comparison.** Is there a stored baseline, or does the agent
   compute one from the previous run?
4. **Artefact retention.** Do assessments live in the repository, or in a separate
   store? Repository is simpler and gives free version history, but adds a commit per
   run unless written to an ignored path.
5. **Model selection and cost tolerance.** What per-run spend is acceptable, and does
   that change the phasing?

---

## 13. Acceptance

v1 is accepted when, on a corpus of at least ten historical commits from PhysicalRisk,
the agent produces a well-formed artefact for every one, and a reviewer judges the
Summary section accurate on each. Accuracy here means: nothing asserted that is untrue,
and nothing material to the change omitted. Elegance of prose is not a criterion.
