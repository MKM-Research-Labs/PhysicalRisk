# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Data lineage manifest — records pipeline step execution with content hashes.

Each step records its inputs, outputs, parameters, and timing so that
downstream consumers can verify data freshness (BCBS 239 Principle 3).
"""

from __future__ import annotations

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
from config import config as _cfg
from config.data_layout import LINEAGE_MANIFEST_FILE

# Override hook: ``None`` means the active catchment's own manifest. Tests set
# it to pin the manifest to a scratch file; nothing else should.
LINEAGE_PATH: Path | None = None


def manifest_path(data_dir: Path | None = None) -> Path:
    """Where the manifest lives: beside the data it describes.

    Each catchment has its own, in its input directory. It used to be a single
    ``data/data_lineage.json`` with no catchment key, which described whichever
    catchment was generated last and made every other one read as drifted.
    ``data_dir`` names a specific tree; without it the active catchment is used.
    """
    if LINEAGE_PATH is not None:
        return Path(LINEAGE_PATH)
    if data_dir is not None:
        return Path(data_dir) / LINEAGE_MANIFEST_FILE
    return _cfg.get_lineage_manifest_path()

from lineage.manifest._topology import (
    DEPENDENCY_GRAPH,
    EXTERNAL_INPUTS,
    OPTIONAL_STEPS,
    STEP_IO,
)

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

def load_manifest(data_dir: Path | None = None) -> dict:
    """Load the lineage manifest, or return an empty skeleton."""
    path = manifest_path(data_dir)
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Corrupt lineage manifest, resetting: %s", exc)
    return {"runs": {}, "steps": {}}


def save_manifest(manifest: dict, data_dir: Path | None = None) -> None:
    """Atomic write — write to temp then rename."""
    path = manifest_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)
        os.replace(tmp, str(path))
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


def pre_hash_inputs(inputs: dict) -> dict:
    """Hash input artifacts *before* a pipeline step runs.

    Call this before the step executes, then pass the result as
    ``input_hashes`` to :func:`record_step`.  This is essential for
    steps that mutate their own input files (e.g. ``synthetic_gauges``
    overwrites ``gauge.json``, ``hazard`` writes back to ``gaugets/``).
    """
    return {k: _hash_artifact(Path(v)) for k, v in inputs.items()}


def record_step(
    step_name: str,
    generator: str,
    inputs: dict,
    outputs: dict,
    parameters: dict,
    elapsed_seconds: float,
    status: str = "success",
    run_id: str | None = None,
    input_hashes: dict | None = None,
) -> dict:
    """Record a pipeline step execution in the manifest.

    *inputs* and *outputs* map logical names to Path objects.

    If *input_hashes* is provided it is used directly (pre-computed hashes
    captured **before** the step ran, which is essential for steps that
    mutate their own input files).  Otherwise inputs are hashed now.

    Returns the step entry that was written.
    """
    run_id = run_id or get_current_run_id()
    manifest = load_manifest()

    if input_hashes is None:
        input_hashes = {k: _hash_artifact(Path(v)) for k, v in inputs.items()}
    output_hashes = {k: _hash_artifact(Path(v)) for k, v in outputs.items()}

    import socket as _socket

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "user": os.environ.get("USER", "unknown"),
        "hostname": _socket.gethostname(),
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
