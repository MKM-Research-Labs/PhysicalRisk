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

"""Per-gauge calibration to observed river levels (MKM-SG-001 / GHD-001 / GH-001 v2).

``catch/<catchment>/gauge_calibration.json`` (built by
``tools/gauge_calibration/build.py`` from Environment Agency records) holds, per
gauge name, a ``sensitivity`` that scales the simulated river rise and the
observed rises at which the alert, warning and severe levels sit. Gauges without
their own record take the file's provisional ``default``.

Three readers keep one picture of each gauge:

* :func:`apply_gauge_calibration` writes the flood levels into ``gauge.json`` as
  normal level + observed rise;
* the gauge-history generator recovers the normal level as alert − alert rise
  (:func:`history_params`) and shrinks its swings by the sensitivity;
* the storm-gauge model shapes each gauge's rise as sensitivity × rise ** exponent
  (a rating curve), so both the size and the spread of floods match the record.

A catchment with no file is untouched: every function returns ``None`` or leaves
the document as it is.
"""

import json
import os
import zlib
from functools import lru_cache
from typing import Dict, Optional

from config import config

FILENAME = "gauge_calibration.json"
OFF_SWITCH = "MKM_GAUGE_CALIBRATION"
# Normal (median) level of a calibrated gauge, on this platform's synthetic datum:
# a fixed value per gauge name in [NORMAL_LEVEL_MIN, NORMAL_LEVEL_MIN + NORMAL_LEVEL_SPAN)
# metres, so re-applying the calibration never moves it.
NORMAL_LEVEL_MIN = 1.5
NORMAL_LEVEL_SPAN = 1.0


@lru_cache(maxsize=None)
def load_gauge_calibration(catchment: Optional[str]) -> Optional[Dict]:
    """The catchment's calibration document, or ``None`` if it has none.

    ``MKM_GAUGE_CALIBRATION=off`` ignores the file — for the uncalibrated
    reference run the calibration itself is derived from.
    """
    if not catchment or os.environ.get(OFF_SWITCH, "").lower() == "off":
        return None
    path = config.get_project_root() / "catch" / catchment.lower() / FILENAME
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def entry_for(calibration: Optional[Dict], gauge_name: Optional[str]) -> Optional[Dict]:
    """The gauge's own entry, else the provisional default, else ``None``."""
    if not calibration:
        return None
    return (calibration.get("gauges") or {}).get(gauge_name) or calibration.get("default")


def normal_level(gauge_name: str) -> float:
    """Fixed normal level for *gauge_name* (deterministic across runs and processes)."""
    frac = (zlib.crc32(gauge_name.encode()) % 1000) / 1000
    return round(NORMAL_LEVEL_MIN + NORMAL_LEVEL_SPAN * frac, 2)


def apply_gauge_calibration(gauge_doc: Dict, calibration: Optional[Dict]) -> int:
    """Rewrite every gauge's flood levels in *gauge_doc* from *calibration*, in place.

    Alert / warning / severe / historical high = normal level + the observed rise.
    Idempotent. Returns the number of gauges updated (0 without a calibration).
    """
    if not calibration or not gauge_doc:
        return 0
    updated = 0
    for record in gauge_doc.get("flood_gauges", []):
        fg = record.get("FloodGauge", record)
        name = fg.get("Header", {}).get("GaugeName")
        entry = entry_for(calibration, name)
        if not entry:
            continue
        base = normal_level(name)
        rise = entry["rise_m"]
        levels = {
            "FloodAlert": round(base + rise["alert"], 2),
            "FloodWarning": round(base + rise["warning"], 2),
            "SevereFloodWarning": round(base + rise["severe"], 2),
            "HistoricalHighLevel": round(base + rise["historical_high"], 2),
        }
        fg.setdefault("FloodStages", {}).update(levels)
        if "historical_high_date" in entry:
            fg["FloodStages"]["HistoricalHighDate"] = entry["historical_high_date"]
        stats = fg.setdefault("SensorStats", {})
        stats["HistoricalHighLevel"] = levels["HistoricalHighLevel"]
        if "historical_high_date" in entry:
            stats["HistoricalHighDate"] = entry["historical_high_date"]
        uk = fg.get("FloodStage", {}).get("UK")
        if isinstance(uk, dict):
            uk.update({k: v for k, v in levels.items() if k != "HistoricalHighLevel"})
        updated += 1
    return updated


def history_params(catchment: Optional[str], gauge_data: Dict) -> Optional[Dict]:
    """``{base_level, variability_scale}`` for the gauge-history generator, or ``None``.

    The normal level is recovered from the calibrated alert level (alert − alert
    rise), so the history and the flood levels agree; the day-to-day and seasonal
    swings shrink by the gauge's sensitivity, as its storm rises do.
    """
    fg = gauge_data.get("FloodGauge", gauge_data)
    entry = entry_for(load_gauge_calibration(catchment), fg.get("Header", {}).get("GaugeName"))
    alert = fg.get("FloodStages", {}).get("FloodAlert")
    if not entry or alert is None:
        return None
    return {"base_level": round(alert - entry["rise_m"]["alert"], 3),
            "variability_scale": entry.get("variability_scale", entry["sensitivity"])}


def sensitivity_for(catchment: Optional[str], gauge_name: Optional[str]) -> float:
    """The storm-gauge sensitivity for *gauge_name* (1.0 when uncalibrated)."""
    entry = entry_for(load_gauge_calibration(catchment), gauge_name)
    return float(entry["sensitivity"]) if entry else 1.0


def rise_exponent_for(catchment: Optional[str], gauge_name: Optional[str]) -> float:
    """The rating-curve exponent for *gauge_name* (1.0, linear, when uncalibrated)."""
    entry = entry_for(load_gauge_calibration(catchment), gauge_name)
    return float(entry.get("rise_exponent", 1.0)) if entry else 1.0
