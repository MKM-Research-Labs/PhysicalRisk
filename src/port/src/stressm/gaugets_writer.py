# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Gaugets population, classifier summary, and pipeline summary helpers.

Extracted from pipeline.py to keep each module under 300 lines.
"""

import json
import time
from pathlib import Path


def populate_gaugets(
    input_dir: Path,
    gauge_params_list: list,
    gauge_ids: list,
    sequence_records: list,
    sequences: list,
    verbose: bool = False,
) -> None:
    """Generate gaugets files: base 168h simulation + storm_responses.

    This replaces the standalone GaugeTimeSeriesGenerator step.  The base
    flood simulation is generated first, then storm_responses from the
    stressm sequence records are appended.  Finally stress_storms.json is
    built from the populated files.

    The result is a complete gaugets/ directory that all downstream
    consumers (propertyts, hazard, animation, stress routes) can use.
    """
    from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
    from port.src.gauge.stress_storms import generate_stress_storms

    print("\n  Generating gaugets (base simulation + storm responses)...", flush=True)

    # Step 1: Generate base 168h flood simulation files
    gen = GaugeTimeSeriesGenerator(input_dir, verbose=verbose)
    result = gen.generate(simulation_hours=168)
    n_gauges = result['data']['num_gauges']
    print(f"    Base simulation: {n_gauges} gauge files  →  gaugets/", flush=True)

    # Step 2: Build per-gauge storm_responses from sequence records
    # Map gauge_id -> index in the gauge_ids list
    gid_to_idx = {gid: i for i, gid in enumerate(gauge_ids)}

    # Build per-gauge response lists
    gauge_responses: dict = {gid: [] for gid in gauge_ids}
    for rec in sequence_records:
        seq_id = rec["sequence_id"]
        peaks = rec["peaks_m"]
        alerts = rec["alert"]
        warnings = rec["warning"]
        severes = rec["severe"]

        for gid, idx in gid_to_idx.items():
            gauge_responses[gid].append({
                "storm_id": seq_id,
                "peak_level_m": peaks[idx],
                "exceeded_alert": alerts[idx],
                "exceeded_warning": warnings[idx],
                "exceeded_severe": severes[idx],
            })

    # Step 3: Merge storm_responses into each gaugets file
    gaugets_dir = input_dir / "gaugets"
    n_updated = 0
    for gid, responses in gauge_responses.items():
        gf = gaugets_dir / f"{gid}.json"
        if not gf.exists():
            continue
        data = json.loads(gf.read_text())
        data["storm_responses"] = {"responses": responses}
        gf.write_text(json.dumps(data, indent=2, separators=(",", ": ")))
        n_updated += 1

    n_alert = sum(1 for r in gauge_responses[gauge_ids[0]]
                  if r["exceeded_alert"]) if gauge_ids else 0
    print(f"    Storm responses: {len(sequence_records):,} sequences × "
          f"{n_updated} gauges merged into gaugets/", flush=True)

    # Step 4: Build stress_storms/ directory from the populated gaugets
    ss_dir = input_dir / "stress_storms"
    ss_result = generate_stress_storms(
        gaugets_dir=gaugets_dir,
        output_dir=ss_dir,
        storms_json_path=input_dir / "storm_sequences.json",
    )
    print(f"    Stress storms: {ss_result['total_storms']} alert-breaching  "
          f"→  stress_storms/", flush=True)


def write_classifier_summary(results: list) -> None:
    """Write training_summary.json to the stressm model dir.

    The summary is in the same format as FloodClassifierTrainer.train_all()
    so FloodPredictor._load_summary() / _get_severe_level() can read it.
    Each result dict comes from train_gauge_stressm_classifier() which
    returns a FloodClassifierTrainer.train_gauge() result dict, so the
    'severe_level' and 'status' fields are present.
    """
    from config import config as _cfg

    trained = [r for r in results if r.get('status') == 'trained']
    avg_auc = (
        sum(r['metrics']['auc_roc'] for r in trained) / len(trained)
        if trained else 0.0
    )
    summary = {
        'num_gauges': len(results),
        'num_trained': len(trained),
        'num_skipped': len(results) - len(trained),
        'avg_auc_roc': round(avg_auc, 4),
        'gauges': results,
    }
    path = _cfg.get_stressm_dir() / 'training_summary.json'
    with open(path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(
        f"  training_summary.json written  "
        f"({len(trained)}/{len(results)} trained  avg AUC: {avg_auc:.4f})",
        flush=True,
    )


def build_summary(
    sequences, type_counts, gauge_params_list,
    alert_count=0, warning_count=0, severe_count=0,
    t_start=None,
) -> dict:
    """Build the return dict for generate_stressm()."""
    n = len(sequences)
    elapsed = time.time() - t_start if t_start else 0
    return {
        "num_sequences": n,
        "num_gauges": len(gauge_params_list),
        "type_counts": type_counts,
        "alert_sequences": alert_count,
        "warning_sequences": warning_count,
        "severe_sequences": severe_count,
        "elapsed_seconds": round(elapsed, 1),
    }
