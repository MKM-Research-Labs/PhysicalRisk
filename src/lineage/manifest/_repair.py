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

"""Manifest repair — re-hash the artifacts on disk and rebuild a consistent manifest."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from lineage.manifest import _core
from lineage.manifest._topology import DEPENDENCY_GRAPH, STEP_IO


def repair_manifest(data_dir: str | Path | None = None) -> dict:
    """Re-hash all on-disk artifacts and rebuild a consistent manifest.

    Walks every step in ``STEP_IO`` in topological order.  For each step
    whose outputs exist on disk, hashes all inputs and outputs and writes
    (or overwrites) the manifest entry so that the recorded hashes match
    the current state of the files.  Steps whose outputs are missing are
    skipped with a warning.

    Existing metadata (run_id, timestamp, generator, parameters) is
    preserved when the step already has a manifest entry; otherwise
    sensible defaults are used.

    Returns a summary dict: ``{"repaired": [...], "skipped": [...]}``.
    """
    from graphlib import TopologicalSorter

    if data_dir is None:
        try:
            from config import PortfolioConfig
            data_dir = Path(PortfolioConfig().get_input_dir())
        except (ImportError, AttributeError):
            # config unavailable (e.g. bootstrap/standalone): derive the default
            # catchment input dir from this file's location.
            catchment = os.getenv("MKM_CATCHMENT", "thames")
            data_dir = Path(__file__).resolve().parents[2] / "data" / "input" / catchment
    else:
        data_dir = Path(data_dir)

    manifest = _core.load_manifest(data_dir)
    run_id = datetime.now().strftime("repair-%Y%m%d-%H%M%S")
    ts_now = datetime.now().isoformat()

    # Topological order
    sorter = TopologicalSorter(DEPENDENCY_GRAPH)
    topo_order = list(sorter.static_order())

    repaired: list[str] = []
    skipped: list[str] = []

    for step_name in topo_order:
        io = STEP_IO.get(step_name)
        if io is None:
            continue

        # Check all outputs exist
        all_outputs_present = True
        for out in io["outputs"]:
            path = data_dir / out
            if out.endswith("/"):
                if not path.is_dir() or not any(path.iterdir()):
                    all_outputs_present = False
                    break
            else:
                if not path.is_file():
                    all_outputs_present = False
                    break

        if not all_outputs_present:
            skipped.append(step_name)
            continue

        # Hash inputs
        input_hashes = {}
        for inp in io["inputs"]:
            path = data_dir / inp
            input_hashes[inp] = _core._hash_artifact(path)

        # Hash outputs
        output_hashes = {}
        for out in io["outputs"]:
            path = data_dir / out
            output_hashes[out] = _core._hash_artifact(path)

        # Preserve existing metadata or use defaults
        existing = manifest.get("steps", {}).get(step_name, {})
        entry = {
            "run_id": existing.get("run_id", run_id),
            "timestamp": existing.get("timestamp", ts_now),
            "generator": existing.get("generator", "unknown"),
            "status": "success",
            "elapsed_seconds": existing.get("elapsed_seconds", 0.0),
            "parameters": existing.get("parameters", {}),
            "inputs": input_hashes,
            "outputs": output_hashes,
        }

        manifest["steps"][step_name] = entry
        repaired.append(step_name)

    # Update runs index
    manifest["runs"][run_id] = repaired
    _core.save_manifest(manifest, data_dir)

    return {"repaired": repaired, "skipped": skipped}
