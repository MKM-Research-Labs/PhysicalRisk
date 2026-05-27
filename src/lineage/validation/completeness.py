# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Pipeline completeness and full-chain validation."""

from __future__ import annotations

from pathlib import Path

from lineage.validation.freshness import check_inputs_fresh


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
    import lineage.validation as _val

    if data_dir is None:
        try:
            from config import PortfolioConfig
            data_dir = Path(PortfolioConfig().get_input_dir())
        except (ImportError, AttributeError):
            import os
            catchment = os.getenv("MKM_CATCHMENT", "thames")
            data_dir = Path(__file__).resolve().parents[3] / "data" / "input" / catchment
    else:
        data_dir = Path(data_dir)

    missing: list[dict] = []
    present = 0
    optional = _val.OPTIONAL_STEPS

    for step_name, io in _val.STEP_IO.items():
        step_missing: list[dict] = []
        step_present = 0
        for output in io["outputs"]:
            path = data_dir / output
            is_dir = output.endswith("/")

            if is_dir:
                if not path.is_dir():
                    step_missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "directory",
                    })
                elif not any(path.iterdir()):
                    step_missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "empty_directory",
                    })
                else:
                    step_present += 1
            else:
                if not path.is_file():
                    step_missing.append({
                        "step": step_name,
                        "output": output,
                        "path": str(path),
                        "type": "file",
                    })
                else:
                    step_present += 1

        # Optional step with ZERO outputs on disk → not enabled for this
        # catchment, skip entirely. If any outputs exist, fall through so
        # partial generation is still flagged as broken.
        if step_name in optional and step_present == 0:
            continue
        missing.extend(step_missing)
        present += step_present

    return {
        "complete": len(missing) == 0,
        "missing": missing,
        "present": present,
        "total": present + len(missing),
    }


def validate_full_chain() -> dict:
    """Run all validation checks and return a summary dict."""
    import lineage.validation as _val

    manifest = _val.load_manifest()
    recorded = set(manifest.get("steps", {}).keys())
    all_steps = set(_val.DEPENDENCY_GRAPH.keys())

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
