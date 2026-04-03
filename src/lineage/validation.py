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
    """Map each output filename to the step that produces it.

    When multiple steps produce the same artifact (e.g. ``gauges`` and
    ``synthetic_gauges`` both output ``gauge.json``), the *last* writer
    in topological order wins — that step's recorded hash is the one
    downstream consumers should match.
    """
    from graphlib import TopologicalSorter

    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    mapping: dict[str, str] = {}
    for step in topo_order:
        io = STEP_IO.get(step)
        if io is None:
            continue
        for out in io["outputs"]:
            mapping[out] = step      # later writers overwrite earlier ones
    return mapping


def _find_producer(step_name: str, artifact: str) -> str | None:
    """Find the correct producer of *artifact* for *step_name*.

    When multiple steps output the same file (e.g. ``gauge.json`` is
    written by both ``gauges`` and ``synthetic_gauges``), the producer
    is the **latest upstream dependency** of *step_name* that outputs
    the artifact.  This ensures each consumer is validated against the
    version of the file it actually consumed at pipeline runtime.
    """
    from graphlib import TopologicalSorter

    # All transitive dependencies of this step
    deps: set[str] = set()
    queue = list(DEPENDENCY_GRAPH.get(step_name, []))
    while queue:
        dep = queue.pop()
        if dep not in deps:
            deps.add(dep)
            queue.extend(DEPENDENCY_GRAPH.get(dep, []))

    # Among dependencies, find all that produce this artifact
    candidates = []
    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    for step in topo_order:
        if step in deps:
            io = STEP_IO.get(step, {})
            if artifact in io.get("outputs", []):
                candidates.append(step)

    # Last in topo order = latest writer among our dependencies
    return candidates[-1] if candidates else None


_MISSING = object()  # sentinel: hash key not present at all


def _current_hash(artifact_name: str, manifest_step: dict):
    """Look up the recorded hash for *artifact_name* in a step's outputs.

    Returns the hash string, ``None`` when the key is explicitly null,
    or ``_MISSING`` when the entry or hash key is absent entirely.
    """
    entry = manifest_step.get("outputs", {}).get(artifact_name)
    if entry and isinstance(entry, dict):
        return entry.get("hash", _MISSING)
    return _MISSING

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _resolve_data_dir() -> Path:
    """Resolve the pipeline data directory."""
    try:
        from config import PortfolioConfig
        return Path(PortfolioConfig().get_input_dir())
    except (ImportError, AttributeError):
        return Path(__file__).resolve().parents[2] / "data" / "input" / "thames"


def _live_hash(artifact: str, data_dir: Path | None = None) -> str | None:
    """Hash an artifact on disk, returning None if it doesn't exist."""
    if data_dir is None:
        data_dir = _resolve_data_dir()
    path = data_dir / artifact
    if path.is_dir() and any(path.iterdir()):
        digest, _ = hash_directory(path)
        return digest
    if path.is_file():
        return hash_file(path)
    return None


def check_inputs_fresh(step_name: str) -> tuple:
    """Check whether every input of *step_name* still matches its producer's
    recorded output hash.

    Returns ``(all_fresh, issues)`` where *issues* is a list of human-readable
    strings describing any mismatches.

    When a recorded hash is ``None`` (artifact was missing at recording time)
    but the file now exists on disk, falls back to a live hash comparison so
    that stale null entries don't block validation indefinitely.
    """
    manifest = load_manifest()
    step_io = STEP_IO.get(step_name)
    if step_io is None:
        return False, [f"Unknown step: {step_name}"]

    # Fallback map for artifacts with no dependency-graph producer
    output_map = _output_step_map()
    issues: list[str] = []
    data_dir: Path | None = None  # lazily resolved

    for inp in step_io["inputs"]:
        # Prefer dependency-aware producer; fall back to global map
        producer = _find_producer(step_name, inp) or output_map.get(inp)
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
        if recorded is _MISSING:
            # Hash key completely absent — no data to compare
            issues.append(
                f"No hash recorded for '{inp}' in step '{producer}'"
            )
            continue
        if recorded is None:
            # Explicitly null (artifact was missing at record time) —
            # fall back to live disk hash so stale nulls don't block forever
            if data_dir is None:
                data_dir = _resolve_data_dir()
            recorded = _live_hash(inp, data_dir)
            if recorded is None:
                issues.append(
                    f"No hash recorded for '{inp}' in step '{producer}' "
                    f"and artifact missing on disk"
                )
                continue

        # Compare with what the consumer recorded at its own run time
        consumer_entry = manifest.get("steps", {}).get(step_name)
        if consumer_entry is None:
            issues.append(f"Step '{step_name}' has never run")
            continue

        consumed = consumer_entry.get("inputs", {}).get(inp, {}).get("hash")
        if consumed is None:
            # Check if hash key exists but is explicitly null vs absent
            inp_entry = consumer_entry.get("inputs", {}).get(inp, {})
            if "hash" in inp_entry and inp_entry["hash"] is None:
                # Explicitly null — fall back to live hash
                if data_dir is None:
                    data_dir = _resolve_data_dir()
                consumed = _live_hash(inp, data_dir)
                if consumed is None:
                    issues.append(
                        f"Step '{step_name}' has no recorded hash for input "
                        f"'{inp}' and artifact missing on disk"
                    )
                    continue
            else:
                issues.append(
                    f"Step '{step_name}' has no recorded hash for input '{inp}'"
                )
                continue

        if consumed != recorded:
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


# ---------------------------------------------------------------------------
# Prerequisite resolution
# ---------------------------------------------------------------------------

def _outputs_exist(step_name: str, data_dir: Path) -> bool:
    """Check whether all outputs of a step exist on disk (non-empty)."""
    io = STEP_IO.get(step_name)
    if io is None:
        return False
    for output in io["outputs"]:
        path = data_dir / output
        if output.endswith("/"):
            if not path.is_dir() or not any(path.iterdir()):
                return False
        else:
            if not path.is_file():
                return False
    return True


def resolve_prerequisites(
    target_steps: list[str],
    data_dir: Path | str | None = None,
) -> list[str]:
    """Return prerequisite steps that need to run before *target_steps*,
    in topological order.

    A prerequisite needs to run if:
    - It has never been recorded in the manifest AND its outputs are
      missing/empty on disk, OR
    - Its inputs are stale (producer hashes changed since last run).

    Skips steps whose outputs already exist on disk even without a
    manifest entry (handles pre-lineage data).

    Args:
        target_steps: Step names the user wants to execute.
        data_dir:     Root data directory (e.g. ``data/input/thames``).

    Returns:
        Ordered list of prerequisite step names that need to run first.
        Empty list if everything is fresh.
    """
    from graphlib import TopologicalSorter

    if data_dir is not None:
        data_dir = Path(data_dir)

    # 1. Collect transitive prerequisites (excluding targets themselves)
    targets = set(target_steps)
    needed: set[str] = set()
    queue: deque[str] = deque()
    for t in target_steps:
        queue.extend(DEPENDENCY_GRAPH.get(t, []))
    while queue:
        dep = queue.popleft()
        if dep not in needed:
            needed.add(dep)
            queue.extend(DEPENDENCY_GRAPH.get(dep, []))
    # Remove targets — we only want prerequisites, not the steps themselves
    needed -= targets

    if not needed:
        return []

    # 2. Filter to only those that are stale or missing
    manifest = load_manifest()
    stale: list[str] = []

    for step in needed:
        step_entry = manifest.get("steps", {}).get(step)
        if step_entry is None:
            # Never recorded — check if outputs exist on disk
            if data_dir and _outputs_exist(step, data_dir):
                continue  # files present, assume OK
            stale.append(step)
        else:
            # Recorded — check if inputs are still fresh
            fresh, _ = check_inputs_fresh(step)
            if not fresh:
                stale.append(step)

    if not stale:
        return []

    # 3. Topological sort of stale steps
    ts = TopologicalSorter()
    for step in stale:
        deps_in_stale = [d for d in DEPENDENCY_GRAPH.get(step, [])
                         if d in stale]
        ts.add(step, *deps_in_stale)

    return list(ts.static_order())


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
