# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Data lineage manifest — records pipeline step execution with content hashes.

Each step records its inputs, outputs, parameters, and timing so that
downstream consumers can verify data freshness (BCBS 239 Principle 3).
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
try:
    from config import config as _cfg
    _project_root = (
        Path(_cfg.get_project_root())
        if hasattr(_cfg, "get_project_root")
        else Path(_cfg.project_root)
    )
except (ImportError, AttributeError):
    _project_root = Path(__file__).resolve().parents[2]

LINEAGE_PATH = _project_root / "data" / "data_lineage.json"

# ---------------------------------------------------------------------------
# Static pipeline topology
# ---------------------------------------------------------------------------
DEPENDENCY_GRAPH = {
    "gauges":         [],
    "properties":     ["gauges"],
    "mortgages":      ["properties"],
    "gaugehd":        ["gauges"],
    "stressm":        ["gauges", "gaugehd"],
    "hazard":         ["gauges", "stressm"],
    "propertyts":     ["properties", "stressm"],
    "propertyhc":     ["propertyts", "hazard"],
    "counterparties": [],
    "blotter":        ["hazard", "counterparties"],
}

STEP_IO = {
    "gauges":         {"inputs": [],
                       "outputs": ["gauge.json"]},
    "properties":     {"inputs": ["gauge.json"],
                       "outputs": ["property.json"]},
    "mortgages":      {"inputs": ["property.json"],
                       "outputs": ["mortgage.json"]},
    "gaugehd":        {"inputs": ["gauge.json"],
                       "outputs": ["gaugehd/"]},
    "stressm":        {"inputs": ["gauge.json", "gaugehd/"],
                       "outputs": ["gaugets/", "stress_storms/",
                                   "storm_sequences.json",
                                   "sequence_gauge_summary.json"]},
    "hazard":         {"inputs": ["gauge.json", "gaugets/"],
                       "outputs": ["gaugehc.json", "gaugets/"]},
    "propertyts":     {"inputs": ["property.json", "gauge.json", "gaugets/"],
                       "outputs": ["propertyts/"]},
    "propertyhc":     {"inputs": ["propertyts/", "gaugehc.json", "gauge.json"],
                       "outputs": ["propertyhc.json"]},
    "counterparties": {"inputs": [],
                       "outputs": ["counterparty.json"]},
    "blotter":        {"inputs": ["gaugehc.json", "counterparty.json"],
                       "outputs": ["prs/"]},
}

# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------
from config.port import LINEAGE_CHUNK_SIZE as _CHUNK  # 64 KB


def hash_file(path: Path) -> str:
    """SHA-256 of a single file, streamed in 64 KB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_directory(dir_path: Path, pattern: str = "*.json") -> tuple:
    """Aggregate hash of sorted(filename + ':' + file_hash) in *dir_path*.

    Returns (hex_digest, file_count).
    """
    h = hashlib.sha256()
    files = sorted(dir_path.glob(pattern))
    for fp in files:
        if fp.is_file():
            h.update(f"{fp.name}:{hash_file(fp)}".encode())
    return h.hexdigest(), len(files)

# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest() -> dict:
    """Load the lineage manifest, or return an empty skeleton."""
    if LINEAGE_PATH.exists():
        try:
            with open(LINEAGE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupt lineage manifest, resetting: %s", exc)
    return {"runs": {}, "steps": {}}


def save_manifest(manifest: dict) -> None:
    """Atomic write — write to temp then rename."""
    LINEAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(LINEAGE_PATH.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)
        os.replace(tmp, str(LINEAGE_PATH))
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

# ---------------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------------

def get_current_run_id() -> str:
    """Generate a run ID from the current timestamp."""
    return datetime.now().strftime("run-%Y%m%d-%H%M%S")


def _hash_artifact(path: Path) -> dict:
    """Hash a file or directory, returning metadata dict."""
    if path.is_dir():
        digest, count = hash_directory(path)
        return {"hash": digest, "file_count": count, "type": "directory"}
    if path.is_file():
        return {"hash": hash_file(path), "type": "file"}
    return {"hash": None, "type": "missing"}


def record_step(
    step_name: str,
    generator: str,
    inputs: dict,
    outputs: dict,
    parameters: dict,
    elapsed_seconds: float,
    status: str = "success",
    run_id: str | None = None,
) -> dict:
    """Record a pipeline step execution in the manifest.

    *inputs* and *outputs* map logical names to Path objects.
    Returns the step entry that was written.
    """
    run_id = run_id or get_current_run_id()
    manifest = load_manifest()

    input_hashes = {k: _hash_artifact(Path(v)) for k, v in inputs.items()}
    output_hashes = {k: _hash_artifact(Path(v)) for k, v in outputs.items()}

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "generator": generator,
        "status": status,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "parameters": parameters,
        "inputs": input_hashes,
        "outputs": output_hashes,
    }

    manifest["steps"][step_name] = entry
    manifest["runs"].setdefault(run_id, []).append(step_name)
    save_manifest(manifest)
    return entry
