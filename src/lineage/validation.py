# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Lineage validation — staleness detection and prerequisite checks.

Supports BCBS 239 Principle 6 (timeliness) by detecting when upstream data
has changed since a downstream step was last executed.
"""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

from lineage.manifest import (
    DEPENDENCY_GRAPH,
    STEP_IO,
    hash_directory,
    hash_file,
    load_manifest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _output_step_map() -> dict:
    """Map each output filename to the step that produces it."""
    mapping: dict[str, str] = {}
    for step, io in STEP_IO.items():
        for out in io["outputs"]:
            mapping[out] = step
    return mapping


def _current_hash(artifact_name: str, manifest_step: dict) -> str | None:
    """Look up the recorded hash for *artifact_name* in a step's outputs."""
    entry = manifest_step.get("outputs", {}).get(artifact_name)
    if entry and isinstance(entry, dict):
        return entry.get("hash")
    return None

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_inputs_fresh(step_name: str) -> tuple:
    """Check whether every input of *step_name* still matches its producer's
    recorded output hash.

    Returns ``(all_fresh, issues)`` where *issues* is a list of human-readable
    strings describing any mismatches.
    """
    manifest = load_manifest()
    step_io = STEP_IO.get(step_name)
    if step_io is None:
        return False, [f"Unknown step: {step_name}"]

    output_map = _output_step_map()
    issues: list[str] = []

    for inp in step_io["inputs"]:
        producer = output_map.get(inp)
        if producer is None:
            issues.append(f"No producer found for input '{inp}'")
            continue

        producer_entry = manifest.get("steps", {}).get(producer)
        if producer_entry is None:
            issues.append(
                f"Producer '{producer}' for input '{inp}' has never run"
            )
            continue

        recorded = _current_hash(inp, producer_entry)
        if recorded is None:
            issues.append(
                f"No hash recorded for '{inp}' in step '{producer}'"
            )
            continue

        # Compare with what the consumer recorded at its own run time
        consumer_entry = manifest.get("steps", {}).get(step_name)
        if consumer_entry is None:
            issues.append(f"Step '{step_name}' has never run")
            continue

        consumed = consumer_entry.get("inputs", {}).get(inp, {}).get("hash")
        if consumed is None:
            issues.append(
                f"Step '{step_name}' has no recorded hash for input '{inp}'"
            )
        elif consumed != recorded:
            issues.append(
                f"Input '{inp}' is stale: producer '{producer}' hash "
                f"changed ({consumed[:12]}.. -> {recorded[:12]}..)"
            )

    return len(issues) == 0, issues


def check_step_prerequisites(step_name: str) -> tuple:
    """Verify that all upstream steps have been recorded in the manifest.

    Returns ``(ok, missing_list)``.
    """
    manifest = load_manifest()
    deps = DEPENDENCY_GRAPH.get(step_name, [])
    missing = [d for d in deps if d not in manifest.get("steps", {})]
    return len(missing) == 0, missing


def get_stale_downstream(step_name: str) -> list:
    """BFS from *step_name* to find all transitive downstream steps."""
    reverse: dict[str, list[str]] = {k: [] for k in DEPENDENCY_GRAPH}
    for step, deps in DEPENDENCY_GRAPH.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(step)

    visited: set[str] = set()
    queue: deque[str] = deque(reverse.get(step_name, []))
    result: list[str] = []

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        result.append(current)
        queue.extend(reverse.get(current, []))

    return result


def validate_full_chain() -> dict:
    """Run all validation checks and return a summary dict."""
    manifest = load_manifest()
    recorded = set(manifest.get("steps", {}).keys())
    all_steps = set(DEPENDENCY_GRAPH.keys())

    missing_steps = sorted(all_steps - recorded)
    stale_steps: list[str] = []
    details: dict[str, list[str]] = {}

    for step in sorted(recorded & all_steps):
        fresh, issues = check_inputs_fresh(step)
        if not fresh:
            stale_steps.append(step)
            details[step] = issues

    return {
        "is_consistent": len(missing_steps) == 0 and len(stale_steps) == 0,
        "stale_steps": stale_steps,
        "missing_steps": missing_steps,
        "details": details,
    }
