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


def check_pipeline_complete(data_dir: Path | str | None = None) -> dict:
    """Verify every pipeline output exists on disk.

    Unlike ``validate_full_chain`` (which checks hash consistency of data
    that *is* present), this function checks that all expected outputs
    from ``STEP_IO`` actually exist.  A missing directory or file is a
    hard failure — the app cannot function without it.

    Args:
        data_dir: Root data directory containing pipeline outputs
                  (e.g. ``data/input/thames``).  If *None*, resolved
                  from config.

    Returns:
        Dict with ``complete`` (bool), ``missing`` (list of
        ``{step, output, path, type}`` dicts), and ``present`` count.
    """
    if data_dir is None:
        try:
            from config import PortfolioConfig
            data_dir = Path(PortfolioConfig().get_input_dir())
        except (ImportError, AttributeError):
            data_dir = Path(__file__).resolve().parents[2] / "data" / "input" / "thames"
    else:
        data_dir = Path(data_dir)

    missing: list[dict] = []
    present = 0

    for step_name, io in STEP_IO.items():
        for output in io["outputs"]:
            path = data_dir / output
            is_dir = output.endswith("/")

            if is_dir:
                if not path.is_dir():
                    missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "directory",
                    })
                elif not any(path.iterdir()):
                    missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "empty_directory",
                    })
                else:
                    present += 1
            else:
                if not path.is_file():
                    missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "file",
                    })
                else:
                    present += 1

    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "present": present,
        "total": present + len(missing),
    }


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
