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


def _merged_summary(summary: dict, result: dict) -> dict:
    """Merge one gauge *result* into a training-summary doc, recomputing aggregates."""
    gauges = [g for g in summary.get("gauges", [])
              if g.get("gauge_id") != result.get("gauge_id")]
    gauges.append(result)
    trained = [g for g in gauges if g.get("status") == "trained"]
    avg_auc = (
        sum(g["metrics"]["auc_roc"] for g in trained) / len(trained)
        if trained else 0.0
    )
    return {
        "num_gauges": len(gauges),
        "num_trained": len(trained),
        "num_skipped": len(gauges) - len(trained),
        "avg_auc_roc": round(avg_auc, 4),
        "gauges": gauges,
    }


def update_training_summary(result: dict, stressm_dir: Path):
    """Merge a single gauge result into ``stressm/training_summary.json`` (file).

    Deliberately stays file-based: this summary lives in the classifier model dir
    and is read by the ``src/models`` flood-classifier predictor, which the
    database migration excludes (analytical models keep their .json). For the
    seam-backed ``classifiers/`` summary used by the trading-stress UI flow, see
    :func:`update_classifier_training_summary`.

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
        summary = {}
    with open(summary_path, "w") as f:
        json.dump(_merged_summary(summary, result), f, indent=2)


def update_classifier_training_summary(result: dict, catchment: str = None):
    """Merge a single gauge result into the ``classifiers/`` training summary
    through the database seam (the trading-stress per-gauge training UI flow)."""
    import database
    catchment = catchment or database.active_catchment()
    summary = database.get_classifier_training_summary(catchment) or {}
    database.save_classifier_training_summary(catchment, _merged_summary(summary, result))


def load_gauge_training_context():
    """Load gauge portfolio, parse gauges, and build spatial model.

    Reads the gauge portfolio and historical (``gaugehd``) baselines for the
    active catchment through the ``database`` seam.

    Returns
    -------
    tuple of (all_gauges, all_gauge_ids, spatial_model)
    """
    import database
    from port.src.storm_multi.models.spatial_correlation import SpatialCorrelationModel

    from .gauge_parser import _extract_gauges, _load_gaugehd_baselines, _parse_gauge

    gauge_json = database.get_gauge_portfolio(database.active_catchment())
    if not gauge_json:
        raise FileNotFoundError("gauge portfolio not found for the active catchment")

    baselines = _load_gaugehd_baselines()
    raw_gauges = _extract_gauges(gauge_json)
    all_gauges = [
        p for r in raw_gauges
        if (p := _parse_gauge(r, baselines)) is not None
    ]

    all_gauge_ids = [g["gauge_id"] for g in all_gauges]
    all_locations = [(g["lat"], g["lon"]) for g in all_gauges]
    spatial_model = SpatialCorrelationModel(all_locations)

    return all_gauges, all_gauge_ids, spatial_model
