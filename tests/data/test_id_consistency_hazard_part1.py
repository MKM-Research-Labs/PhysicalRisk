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

"""Hazard curve data quality and cross-entity consistency (part 1)."""

import json
from pathlib import Path

import pytest

from tests.data._id_consistency_helpers import (
    INPUT_DIR,
    _load_gauge_ids,
    _load_property_ids,
    _load_counterparty_ids,
    _load_trade_counterparty_ids,
    _load_trade_ids,
    _load_propertyhc_ids,
    _load_propertyshd_ids,
    _load_propertyshe_ids,
    CATCHMENT_LAT_BOUNDS,
    CATCHMENT_LON_BOUNDS,
)


def _load_gaugehc():
    """Load raw gaugehc.json data."""
    path = INPUT_DIR / "gaugehc.json"
    if not path.exists():
        return {}
    return json.load(open(path)).get("hazard_curves", {})


def _load_gauge_records():
    """Load raw gauge records from gauge.json."""
    path = INPUT_DIR / "gauge.json"
    if not path.exists():
        return []
    return json.load(open(path)).get("flood_gauges", [])


# =========================================================================
# Gauge hazard curve quality
# =========================================================================

class TestGaugeHazardCurveQuality:
    """gaugehc.json hazard curves must be complete and physically consistent."""

    def test_count_matches_gauges(self):
        """Number of hazard curves must match number of gauges."""
        gauge_ids = _load_gauge_ids()
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        assert len(hc) == len(gauge_ids), (
            f"gaugehc.json has {len(hc)} curves but gauge.json has "
            f"{len(gauge_ids)} gauges. Regenerate: python app.py port --hazard"
        )

    def test_gev_params_present_and_numeric(self):
        """Every hazard curve must have numeric GEV parameters."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        bad = []
        for gid, curve in hc.items():
            # GEV params are flat keys: gev_location, gev_scale, gev_shape
            for param in ("gev_location", "gev_scale", "gev_shape"):
                val = curve.get(param)
                if val is None or not isinstance(val, (int, float)):
                    bad.append(f"{gid}.{param}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} curves have missing/non-numeric GEV params: "
            f"{bad[:5]}. Regenerate hazard curves."
        )

    def test_curve_points_non_empty(self):
        """Every hazard curve must have at least one curve point."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        empty = [gid for gid, c in hc.items()
                 if not c.get("curve_points")]
        assert len(empty) == 0, (
            f"{len(empty)} curves have no curve_points: {empty[:5]}"
        )

    def test_return_periods_monotonic_increasing(self):
        """Return periods within each curve must be monotonically increasing."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        bad = []
        for gid, curve in hc.items():
            pts = curve.get("curve_points", [])
            rps = [p.get("return_period_years", 0) for p in pts]
            if len(rps) > 1 and any(rps[i] >= rps[i + 1] for i in range(len(rps) - 1)):
                bad.append(gid)
        assert len(bad) == 0, (
            f"{len(bad)} curves have non-monotonic return periods: "
            f"{bad[:5]}. Hazard curve fitting may have failed."
        )

    def test_exceedance_probs_monotonic_decreasing(self):
        """Annual exceedance probabilities must decrease with return period."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        bad = []
        for gid, curve in hc.items():
            pts = curve.get("curve_points", [])
            probs = [p.get("annual_exceedance_prob", 0) for p in pts]
            if len(probs) > 1 and any(probs[i] <= probs[i + 1] for i in range(len(probs) - 1)):
                bad.append(gid)
        assert len(bad) == 0, (
            f"{len(bad)} curves have non-decreasing exceedance probs: "
            f"{bad[:5]}. Check hazard curve generation."
        )

    def test_exceedance_rates_bounded(self):
        """All annual exceedance probabilities must be in (0, 1)."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        bad = []
        for gid, curve in hc.items():
            for pt in curve.get("curve_points", []):
                p = pt.get("annual_exceedance_prob", -1)
                if not (0 < p < 1):
                    bad.append(f"{gid}={p}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} curves have out-of-range exceedance probs: "
            f"{bad[:5]}. Expected (0, 1)."
        )


# =========================================================================
# Gauge flood thresholds
# =========================================================================

class TestGaugeFloodThresholds:
    """Gauge flood stage thresholds and metadata must be valid."""

    def test_thresholds_ordered(self):
        """FloodAlert < FloodWarning < SevereFloodWarning for each gauge."""
        records = _load_gauge_records()
        if not records:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in records:
            fg = g.get("FloodGauge", g)
            gid = fg.get("Header", {}).get("GaugeID", "?")
            uk = fg.get("FloodStage", {}).get("UK", {})
            fa = uk.get("FloodAlert", 0)
            fw = uk.get("FloodWarning", 0)
            sfw = uk.get("SevereFloodWarning", 0)
            if not (fa < fw < sfw):
                bad.append(f"{gid}: {fa}<{fw}<{sfw}")
        assert len(bad) == 0, (
            f"{len(bad)} gauges have mis-ordered thresholds: {bad[:5]}. "
            "Expected Alert < Warning < Severe."
        )

    def test_thresholds_positive(self):
        """All flood thresholds must be > 0."""
        records = _load_gauge_records()
        if not records:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in records:
            fg = g.get("FloodGauge", g)
            gid = fg.get("Header", {}).get("GaugeID", "?")
            uk = fg.get("FloodStage", {}).get("UK", {})
            for key in ("FloodAlert", "FloodWarning", "SevereFloodWarning"):
                val = uk.get(key, 0)
                if val <= 0:
                    bad.append(f"{gid}.{key}={val}")
                    break
        assert len(bad) == 0, (
            f"{len(bad)} gauges have non-positive thresholds: {bad[:5]}"
        )

    def test_coords_in_catchment_bounds(self):
        """Gauge coordinates must fall within the active catchment's bounds."""
        records = _load_gauge_records()
        if not records:
            pytest.skip("gauge.json empty or missing")
        bad = []
        for g in records:
            fg = g.get("FloodGauge", g)
            gid = fg.get("Header", {}).get("GaugeID", "?")
            info = (fg.get("SensorDetails", {})
                      .get("GaugeInformation", {}))
            lat = info.get("GaugeLatitude", 0)
            lon = info.get("GaugeLongitude", 0)
            if not (CATCHMENT_LAT_BOUNDS[0] <= lat <= CATCHMENT_LAT_BOUNDS[1]):
                bad.append(f"{gid} lat={lat}")
            elif not (CATCHMENT_LON_BOUNDS[0] <= lon <= CATCHMENT_LON_BOUNDS[1]):
                bad.append(f"{gid} lon={lon}")
        assert len(bad) == 0, (
            f"{len(bad)} gauges outside catchment bounds: {bad[:5]}. "
            f"Expected lat {CATCHMENT_LAT_BOUNDS}, lon {CATCHMENT_LON_BOUNDS}."
        )

    def test_gauge_names_non_empty(self):
        """Every gauge must have a non-empty gauge name."""
        hc = _load_gaugehc()
        if not hc:
            pytest.skip("gaugehc.json not generated yet")
        empty = [gid for gid, c in hc.items()
                 if not c.get("gauge_name", "").strip()]
        assert len(empty) == 0, (
            f"{len(empty)} hazard curves have empty gauge_name: {empty[:5]}"
        )
