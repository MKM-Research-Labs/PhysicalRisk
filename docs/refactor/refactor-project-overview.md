# Project Overview — Module Boundary Migration

A standing plan for migrating the flood simulator's utility and function layer from a line-count rule to a single-responsibility and dependency rule, while producing an inventory that doubles as audit and model-validation evidence.

This document is written to be picked up cold after a break. It states the goal, the rule, the per-file artifact, the sequence, and the working loop, so work can resume without reconstructing the reasoning.

## Goal

Reduce technical debt in a complex storm and flood simulator with pricing and hedging capability. The refactor serves five standing objectives at once, and every decision below is chosen to advance them together rather than trade between them.

Package large files into cohesive modules. Reach full test coverage. Hold full audit compliance. Meet BCBS 239. Meet model-validation requirements. Minimise duplication.

These are not five separate workstreams. They are the same discipline — clean boundaries — seen from five angles. A module with one responsibility and a narrow interface is the unit that gets tested through its interface, audited in isolation, traced for lineage, and freed of duplicated logic. Draw the boundary once and all five advance.

## The rule that replaces the line count

The 300-line rule was a good starter. It surfaced grab-bag files and gave a mechanical trigger to break them up. It has done its job and now works against the codebase in two ways. It pushes cohesive logic apart when a responsibility legitimately runs long, and it says nothing about coupling between the files it produces.

The replacement rule: a module contains one responsibility, exposes a narrow interface, and depends in one direction.

Three tests decide whether a module is correctly bounded.

Single responsibility. State what it does in one sentence with no "and". An "and" means more than one module wearing one filename.

Narrow interface. The module is used through a small number of public entry points. If callers reach past them into internals, the boundary is fictional.

One-directional dependency. It depends on things below and is depended on by things above. Two modules importing each other, directly or through a cycle, are one responsibility split prematurely. Recombine them, or extract the shared piece beneath both.

Length is now a smell, not a limit. A file past roughly 400 to 500 lines prompts the question "what distinct responsibilities live here and do they separate cleanly". Sometimes the answer is one responsibility at its natural size, and it stays. A file past 1,000 lines carries a strong prior toward splitting, but the split still follows the responsibility seam, never an arbitrary line.

The failure mode to avoid is cutting a cohesive 600-line module into six entangled 100-line files. That satisfies a line rule and violates every rule that matters, for both a human reader and a model trying to hold the subsystem in context.

## Scope

In scope: functions, utilities, helper modules. Extraction is cheap here and cohesion is what is at risk.

Out of scope: `src/port`. Those functions are lengthy by design because each expresses a single sequential process end to end. Breaking them apart fragments a linear flow into indirection that is harder to audit, not easier. Their length is an asset for audit and they are left alone.

## Per-file artifact

Every file walked gets one entry in a fixed schema. The schema matters as much as the refactor, because consistent entries aggregate into the module inventory that model validation and BCBS 239 want to see. Improvised per-file notes will not aggregate; a fixed schema will.

Each entry records:

Responsibility. The one-sentence statement, no "and". This is the pass/fail gate and doubles as the module docstring.

Public interface. The entry points callers are meant to use, with signatures and IO types.

Dependencies. What it imports (in) and what imports it (out), so direction is visible and cycles are obvious.

IO and side effects. Files read and written, config touched, external state. This is what BCBS 239 lineage and model validation care about most, so it is captured for every module rather than only the numerical ones.

Verdict. Passes the three tests, or the specific violation and the planned action — recombine, extract, or leave.

Source of truth is the per-file docstring, kept beside the code so it stays current. The central register is generated from those docstrings so the whole inventory can be audited at once without drifting from the code.

## Sequence

Walk the tree dependency-leaves-first. Start with modules nothing imports, or that only depend on utilities, and move upward toward orchestration last.

Leaves-first because fixing a leaf disturbs nothing above it, and by the time the orchestration layer is reached its dependencies are already clean. Top-down would mean refactoring against foundations still in motion.

Before starting, remove the 300-line rule from any lint or CI check that enforces it, so it stops forcing bad splits during the migration itself.

First pass targets the files the old rule most distorted — fragments split under 300 lines that read as one thing — and recombines those that share a responsibility. Second pass targets the files the old rule missed, the long ones over the smell threshold, inspecting each for responsibilities to lift along clean seams.

## Working loop, per file

One file at a time, resumable across weeks.

1. Read the file. Produce the schema entry — responsibility, interface, dependencies, IO, verdict.
2. Check the entry against the three tests.
3. If it passes, mark it clean and record the responsibility statement as the docstring.
4. If it fails, write the extraction or recombination plan, naming the clean seam and confirming the split introduces no import cycle.
5. Apply the change, confirm tests still pass, then move to the next leaf.

Over an extended period the inventory builds itself, and what it builds is simultaneously the refactor, the test-coverage map, the duplication register, and the audit and validation evidence.

## Open decisions to settle on resumption

Whether the responsibility sentence is enforced anywhere — a required docstring checked in CI — or adopted by convention.

Whether the central register is the only aggregate view or whether a dependency graph is generated alongside it to make cycles visually obvious across the whole tree.
