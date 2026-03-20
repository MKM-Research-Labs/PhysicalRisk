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

"""Gauge JSON parsing utilities for the multi-storm stress pipeline."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _extract_gauges(gauge_json: dict) -> List[dict]:
    """Extract gauge records from gauge.json regardless of schema variant."""
    raw = gauge_json.get("flood_gauges", [])
    if isinstance(raw, list):
        return raw
    # dict keyed by gauge_id
    return list(raw.values())


def _load_gaugehd_baselines(gaugehd_dir: Path) -> Dict[str, Dict]:
    """Load historical baselines from each gaugehd file.

    Returns:
        Dict mapping gauge_id → {
            'mean_level': float,
            'monthly_means': {'01': float, ..., '12': float} or None,
        }
    """
    baselines: Dict[str, Dict] = {}
    if not gaugehd_dir.exists():
        return baselines
    for f in gaugehd_dir.glob("gauge_*_hd.json"):
        try:
            data = json.loads(f.read_text())
            gid = data.get("gauge_metadata", {}).get("gauge_id")
            stats = data.get("statistics", {})
            mean = stats.get("mean_level")
            if gid and mean is not None:
                baselines[gid] = {
                    "mean_level": float(mean),
                    "monthly_means": stats.get("monthly_means"),
                }
        except Exception:
            continue
    if baselines:
        logger.info("Loaded %d gauge baselines from gaugehd/", len(baselines))
    return baselines


def _seasonal_base_level(monthly_means: Optional[Dict[str, float]],
                          mean_level: float,
                          month: int) -> float:
    """Return the base level for a given month using historical monthly means.

    Falls back to the annual mean if monthly data is unavailable.
    """
    if monthly_means:
        key = f"{month:02d}"
        return float(monthly_means.get(key, mean_level))
    return mean_level


def _parse_gauge(record: dict, baselines: Optional[Dict[str, Dict]] = None) -> Optional[dict]:
    """
    Return a normalised gauge dict with keys:
      gauge_id, lat, lon, base_level, monthly_means, flood_alert,
      flood_warning, severe_warning

    If gaugehd baselines are provided, base_level uses the historical mean
    daily water level and monthly_means enables seasonal variation.
    Otherwise falls back to 0.35 × flood_alert.

    Returns None if the record is missing critical fields.
    """
    fg = record.get("FloodGauge", record)  # handle nested or flat schema
    header = fg.get("Header", {})
    loc = fg.get("Location", fg.get("SensorDetails", {}).get("GaugeInformation", {}))
    stages = fg.get("FloodStages", fg.get("FloodStage", {}).get("UK", {}))

    gauge_id = header.get("GaugeID") or fg.get("gauge_id")
    lat = loc.get("GaugeLatitude") or loc.get("latitude")
    lon = loc.get("GaugeLongitude") or loc.get("longitude")
    alert = stages.get("FloodAlert") or stages.get("flood_alert_m")
    warning = stages.get("FloodWarning") or stages.get("flood_warning_m")
    severe = stages.get("SevereFloodWarning") or stages.get("severe_flood_warning_m")

    if not all([gauge_id, lat is not None, lon is not None, alert]):
        return None

    # Base level: prefer historical mean from gaugehd, fall back to heuristic
    monthly_means = None
    if baselines and gauge_id in baselines:
        base_level = baselines[gauge_id]["mean_level"]
        monthly_means = baselines[gauge_id].get("monthly_means")
    else:
        base_level = float(alert) * 0.35

    flood_warning = float(warning) if warning else float(alert) * 1.33
    severe_warning = float(severe) if severe else float(alert) * 1.58

    return {
        "gauge_id": gauge_id,
        "lat": float(lat),
        "lon": float(lon),
        "base_level": base_level,
        "monthly_means": monthly_means,
        "flood_alert": float(alert),
        "flood_warning": flood_warning,
        "severe_warning": severe_warning,
    }
