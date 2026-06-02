# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Hazard curve data quality and cross-entity consistency."""

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


def _load_propertyhc_data():
    """Load raw propertyhc.json data."""
    path = INPUT_DIR / "propertyhc.json"
    if not path.exists():
        return {}
    return json.load(open(path)).get("property_hazard_curves", {})


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


# =========================================================================
# Property hazard curves
# =========================================================================

class TestPropertyHazardCurves:
    """propertyhc.json must be consistent with property.json."""

    def test_propertyhc_count_matches(self):
        """propertyhc.json must have one entry per property."""
        prop_ids = _load_property_ids()
        phc_ids = _load_propertyhc_ids()
        if not phc_ids:
            pytest.skip("propertyhc.json not generated yet")
        assert len(phc_ids) == len(prop_ids), (
            f"propertyhc.json has {len(phc_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate: python app.py port --propertyhc"
        )

    def test_propertyhc_ids_match(self):
        """propertyhc.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        phc_ids = _load_propertyhc_ids()
        if not phc_ids:
            pytest.skip("propertyhc.json not generated yet")
        missing = prop_ids - phc_ids
        extra = phc_ids - prop_ids
        assert len(missing) == 0 and len(extra) == 0, (
            f"propertyhc.json ID mismatch: {len(missing)} missing, "
            f"{len(extra)} extra. Missing: {sorted(missing)[:3]}, "
            f"Extra: {sorted(extra)[:3]}"
        )

    def test_term_structure_exists(self):
        """Every property hazard curve must contain a term_structure."""
        phc = _load_propertyhc_data()
        if not phc:
            pytest.skip("propertyhc.json not generated yet")
        missing = [pid for pid, c in phc.items()
                   if not c.get("term_structure")]
        assert len(missing) == 0, (
            f"{len(missing)} property hazard curves lack term_structure: "
            f"{missing[:5]}"
        )

    def test_severe_trigger_present(self):
        """Every property hazard curve must have a severe flood trigger level."""
        phc = _load_propertyhc_data()
        if not phc:
            pytest.skip("propertyhc.json not generated yet")
        missing = []
        for pid, c in phc.items():
            ts = c.get("term_structure", {})
            if "severe" not in ts:
                missing.append(pid)
        assert len(missing) == 0, (
            f"{len(missing)} property hazard curves lack severe_trigger: "
            f"{missing[:5]}"
        )


# =========================================================================
# Property hazard derived (SHD / SHE)
# =========================================================================

class TestPropertyHazardDerived:
    """propertyshd.json and propertyshe.json must match property.json."""

    def test_propertyshd_count_matches(self):
        """propertyshd.json must have one entry per property."""
        prop_ids = _load_property_ids()
        shd_ids = _load_propertyshd_ids()
        if not shd_ids:
            pytest.skip("propertyshd.json not generated yet")
        assert len(shd_ids) == len(prop_ids), (
            f"propertyshd.json has {len(shd_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate."
        )

    def test_propertyshe_count_matches(self):
        """propertyshe.json must have one entry per property."""
        prop_ids = _load_property_ids()
        she_ids = _load_propertyshe_ids()
        if not she_ids:
            pytest.skip("propertyshe.json not generated yet")
        assert len(she_ids) == len(prop_ids), (
            f"propertyshe.json has {len(she_ids)} entries but property.json "
            f"has {len(prop_ids)}. Regenerate."
        )

    def test_propertyshd_ids_match(self):
        """propertyshd.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        shd_ids = _load_propertyshd_ids()
        if not shd_ids:
            pytest.skip("propertyshd.json not generated yet")
        missing = prop_ids - shd_ids
        assert len(missing) == 0, (
            f"{len(missing)} properties missing from propertyshd.json: "
            f"{sorted(missing)[:5]}"
        )

    def test_propertyshe_ids_match(self):
        """propertyshe.json IDs must match property.json IDs."""
        prop_ids = _load_property_ids()
        she_ids = _load_propertyshe_ids()
        if not she_ids:
            pytest.skip("propertyshe.json not generated yet")
        missing = prop_ids - she_ids
        assert len(missing) == 0, (
            f"{len(missing)} properties missing from propertyshe.json: "
            f"{sorted(missing)[:5]}"
        )
