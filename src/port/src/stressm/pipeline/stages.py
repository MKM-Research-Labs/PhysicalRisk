# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Pipeline output stages: write results and train classifiers."""

import json
import logging
from pathlib import Path

import numpy as np

from ._constants import GAUGE_SUMMARY_FILENAME, GAUGE_SUMMARY_DIR, SCHEMA_VERSION_SPATIAL
from ..gaugets_writer import populate_gaugets, write_classifier_summary
from ..reporting import _print_gauge_progression
from ..classifier import train_gauge_stressm_classifier, _print_classifier_result

logger = logging.getLogger(__name__)


def write_gaugets(input_dir, gauge_params_list, gauge_ids,
                  sequence_records, sequences, verbose):
    """Stage 4b: Generate gaugets (base simulation + storm responses)."""
    populate_gaugets(
        input_dir, gauge_params_list, gauge_ids,
        sequence_records, sequences, verbose,
    )


def write_single_gauge_output(input_dir, catchment_id, count, n_gauges,
                              gauge_ids, gauge_id, sequence_records):
    """Write single-gauge output file (used by classifier training)."""
    summary_doc = {
        "schema_version": SCHEMA_VERSION_SPATIAL,
        "catchment_id": catchment_id,
        "num_sequences": count,
        "num_gauges": n_gauges,
        "gauge_ids": gauge_ids,
        "sequences": sequence_records,
    }
    out_path = input_dir / f"sequence_gauge_{gauge_id}.json"
    with open(out_path, "w") as f:
        json.dump(summary_doc, f, indent=2)
    size_mb = out_path.stat().st_size / 1_048_576
    print(f"  ->  {out_path.name}  ({size_mb:.1f} MB)", flush=True)


def write_split_output(input_dir, catchment_id, count, n_gauges,
                       gauge_ids, sequence_records):
    """Write split-mode output: sequence_gauge/ directory with per-gauge files."""
    import shutil

    sg_dir = input_dir / GAUGE_SUMMARY_DIR
    if sg_dir.exists():
        shutil.rmtree(sg_dir)
    sg_dir.mkdir(parents=True)

    # Write _index.json (metadata only — no per-gauge arrays)
    index_doc = {
        "schema_version": SCHEMA_VERSION_SPATIAL,
        "catchment_id": catchment_id,
        "num_sequences": count,
        "num_gauges": n_gauges,
        "gauge_ids": gauge_ids,
        "sequences": [
            {
                "sequence_id": r["sequence_id"],
                "sequence_type": r["sequence_type"],
                "intensity_category": r["intensity_category"],
                "num_storms": r["num_storms"],
                "total_precip_mm": r["total_precip_mm"],
            }
            for r in sequence_records
        ],
    }
    index_path = sg_dir / "_index.json"
    with open(index_path, "w") as f:
        json.dump(index_doc, f, separators=(",", ":"))

    # Write per-gauge files
    for gi, gid in enumerate(gauge_ids):
        gauge_doc = {
            "gauge_id": gid,
            "num_sequences": count,
            "sequences": [
                {
                    "sequence_id": r["sequence_id"],
                    "peak_m": r["peaks_m"][gi],
                    "peak_hour": r["peak_hours"][gi],
                    "alert": r["alert"][gi],
                    "warning": r["warning"][gi],
                    "severe": r["severe"][gi],
                    "pulse_peaks": r["pulse_peaks"][gi],
                    "sequence_type": r["sequence_type"],
                    "num_storms": r["num_storms"],
                }
                for r in sequence_records
            ],
        }
        gauge_path = sg_dir / f"{gid}.json"
        with open(gauge_path, "w") as f:
            json.dump(gauge_doc, f, separators=(",", ":"))

    # Remove legacy monolithic file if present
    legacy_path = input_dir / GAUGE_SUMMARY_FILENAME
    if legacy_path.exists():
        legacy_path.unlink()

    total_mb = sum(
        p.stat().st_size for p in sg_dir.iterdir()
    ) / 1_048_576
    print(f"  ->  {GAUGE_SUMMARY_DIR}/  ({n_gauges + 1} files, "
          f"{total_mb:.1f} MB)", flush=True)


def run_classifier_training(*, single_gauge_mode, gauge_id, gauge_params_list,
                            sequence_records, count, sequences, spatial_model,
                            target_indices, output_dir, seed, n_gauges,
                            train_classifier):
    """Run optional classifier training (single-gauge or full-portfolio)."""
    if single_gauge_mode:
        _print_gauge_progression(gauge_params_list[0], sequence_records, count)
        if train_classifier:
            clf_result = train_gauge_stressm_classifier(
                sequences=sequences,
                gauge=gauge_params_list[0],
                spatial_model=spatial_model,
                target_spatial_index=target_indices[0],
                output_dir=output_dir,
                rng=np.random.RandomState(seed + 1),
            )
            _print_classifier_result(clf_result)
            write_classifier_summary([clf_result])
    elif train_classifier:
        import time
        print(f"\n  Training multi-storm classifiers for {n_gauges} gauges...", flush=True)
        t4 = time.time()
        n_trained = n_failed = 0
        clf_results = []
        for i, (gauge, spatial_i) in enumerate(zip(gauge_params_list, target_indices)):
            try:
                clf_result = train_gauge_stressm_classifier(
                    sequences=sequences,
                    gauge=gauge,
                    spatial_model=spatial_model,
                    target_spatial_index=spatial_i,
                    output_dir=output_dir,
                    rng=np.random.RandomState(seed + 1 + i),
                )
                _print_classifier_result(clf_result)
                clf_results.append(clf_result)
                n_trained += 1
            except Exception as exc:
                print(f"  [{gauge['gauge_id']}] classifier failed: {exc}", flush=True)
                n_failed += 1
        t5 = time.time()
        print(
            f"\n  Classifiers: {n_trained} trained, {n_failed} failed  "
            f"({(t5 - t4) / 60:.1f} min)",
            flush=True,
        )
        if clf_results:
            write_classifier_summary(clf_results)
