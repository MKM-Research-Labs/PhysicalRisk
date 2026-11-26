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

"""Gauge responses from the Storm-Gauge Response Model (MKM-SG-001) — GH-001 v2.0.

Up to v1 the hazard stage routed every storm through its own simple response
model (``response_model.GaugeResponseModel``) and overwrote the storm-gauge
model's results. From v2.0 the GEV curves are built from the storm-gauge model's
peaks, so one river model — the one calibrated to observed levels — drives the
hazard curves, the spreads and everything downstream.

The storm-gauge stage keeps, per gauge, each sequence's per-storm peaks
(``sequence_gauge`` → ``pulse_peaks``). Each becomes one ``GaugeResponse`` keyed
by the member storm's id, which is what the event catalogue groups on.
"""

import logging
from typing import Dict, List, Optional

import database

from ..data_structures import GaugeResponse

logger = logging.getLogger(__name__)


def _member_ids(sequences_data: dict) -> Dict[str, List[str]]:
    """sequence_id → its member storm ids, in storm order."""
    return {s["sequence_id"]: [m["storm_id"] for m in s.get("storms") or []]
            for s in sequences_data.get("sequences", []) if s.get("sequence_id")}


def _normal_levels(catchment: str, gauges: List[dict]) -> Dict[str, float]:
    """Each gauge's normal level as the storm-gauge model used it (history mean,
    else 0.35 × alert), so ``level_change_m`` is the rise it simulated."""
    from port.src.stressm.gauge_parser import _load_gaugehd_baselines
    baselines = _load_gaugehd_baselines(catchment)
    return {g["gauge_id"]: (baselines[g["gauge_id"]]["mean_level"] if g["gauge_id"] in baselines
                            else (g.get("flood_alert") or 0.0) * 0.35)
            for g in gauges}


def load_stressm_responses(
    catchment: str,
    sequences_data: dict,
    gauges: List[dict],
) -> Optional[Dict[str, List[GaugeResponse]]]:
    """Per-gauge, per-storm responses from the storm-gauge model, or ``None`` if
    any gauge has no ``sequence_gauge`` record (the storm-gauge stage hasn't run
    for this portfolio)."""
    members = _member_ids(sequences_data)
    normal = _normal_levels(catchment, gauges)
    out: Dict[str, List[GaugeResponse]] = {}
    for g in gauges:
        gid = g["gauge_id"]
        record = database.get_sequence_gauge(catchment, gid)
        if not record:
            logger.warning("No storm-gauge responses for %s", gid)
            return None
        alert, warning, severe = g["flood_alert"], g["flood_warning"], g["severe_flood_warning"]
        base = normal[gid]
        rows: List[GaugeResponse] = []
        for seq in record.get("sequences", []):
            ids = members.get(seq["sequence_id"]) or []
            pulses = seq.get("pulse_peaks") or ([{"storm_index": 0, "peak_m": seq["peak_m"]}]
                                                if ids else [])
            for p in pulses:
                i = p["storm_index"]
                if i >= len(ids):
                    continue
                peak = float(p["peak_m"])
                rows.append(GaugeResponse(
                    gauge_id=gid, storm_id=ids[i], base_level_m=base,
                    level_change_m=peak - base, peak_level_m=peak,
                    exceeded_alert=peak >= alert, exceeded_warning=peak >= warning,
                    exceeded_severe=peak >= severe))
        out[gid] = rows
    return out
