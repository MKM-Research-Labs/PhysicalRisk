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

"""Shared training summary I/O and data loading for classifier results."""

import json
from pathlib import Path


def update_training_summary(result: dict, stressm_dir: Path):
    """Merge a single gauge result into training_summary.json (incremental save).

    Parameters
    ----------
    result : dict
        Single gauge training result with at least ``gauge_id`` and ``status``.
    stressm_dir : Path
        Directory containing (or to contain) ``training_summary.json``.
    """
    summary_path = stressm_dir / "training_summary.json"

    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
    else:
        summary = {"num_gauges": 0, "num_trained": 0,
                   "num_skipped": 0, "avg_auc_roc": 0, "gauges": []}

    gauges = [g for g in summary.get("gauges", [])
              if g.get("gauge_id") != result.get("gauge_id")]
    gauges.append(result)

    trained = [g for g in gauges if g.get("status") == "trained"]
    avg_auc = (
        sum(g["metrics"]["auc_roc"] for g in trained) / len(trained)
        if trained else 0.0
    )
    summary["num_gauges"] = len(gauges)
    summary["num_trained"] = len(trained)
    summary["num_skipped"] = len(gauges) - len(trained)
    summary["avg_auc_roc"] = round(avg_auc, 4)
    summary["gauges"] = gauges

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)


def load_gauge_training_context(input_dir: Path):
    """Load gauge portfolio, parse gauges, and build spatial model.

    Parameters
    ----------
    input_dir : Path
        data/input/<catchment>/ containing gauge.json and gaugehd/.

    Returns
    -------
    tuple of (all_gauges, all_gauge_ids, spatial_model)
    """
    from .gauge_parser import _extract_gauges, _parse_gauge, _load_gaugehd_baselines
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel

    gauge_path = input_dir / "gauge.json"
    if not gauge_path.exists():
        raise FileNotFoundError(f"gauge.json not found at {gauge_path}")

    with open(gauge_path) as f:
        gauge_json = json.load(f)

    baselines = _load_gaugehd_baselines(input_dir / "gaugehd")
    raw_gauges = _extract_gauges(gauge_json)
    all_gauges = [
        p for r in raw_gauges
        if (p := _parse_gauge(r, baselines)) is not None
    ]

    all_gauge_ids = [g["gauge_id"] for g in all_gauges]
    all_locations = [(g["lat"], g["lon"]) for g in all_gauges]
    spatial_model = SpatialCorrelationModel(all_locations)

    return all_gauges, all_gauge_ids, spatial_model
