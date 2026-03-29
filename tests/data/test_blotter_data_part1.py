# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Data availability tests — Blotter (part 1).

Gauge hazard curves (gaugehc.json), market state (market_state.json).
"""

import json

import pytest

from tests.data.conftest import (
    GAUGEHC_PATH,
    MARKET_STATE,
    GAUGE_REQUIRED_FIELDS,
    MARKET_STATE_REQUIRED_KEYS,
    YIELD_CURVE_TENORS,
)


# ---------------------------------------------------------------------------
# Gauge hazard curves (gaugehc.json)
# ---------------------------------------------------------------------------

class TestGaugehcData:
    """gaugehc.json must exist and contain valid hazard curve data for all gauges."""

    @pytest.fixture(scope="class")
    def gaugehc(self):
        assert GAUGEHC_PATH.exists(), f"gaugehc.json not found at {GAUGEHC_PATH}"
        return json.loads(GAUGEHC_PATH.read_text())

    def test_file_exists(self):
        assert GAUGEHC_PATH.exists(), f"Missing: {GAUGEHC_PATH}"

    def test_has_hazard_curves_key(self, gaugehc):
        assert "hazard_curves" in gaugehc, "gaugehc.json missing top-level 'hazard_curves' key"

    def test_gauge_count_at_least_40(self, gaugehc):
        count = len(gaugehc["hazard_curves"])
        assert count >= 40, f"Expected at least 40 gauges, got {count}"

    def test_each_gauge_has_required_fields(self, gaugehc):
        missing = {}
        for gid, g in gaugehc["hazard_curves"].items():
            absent = GAUGE_REQUIRED_FIELDS - set(g.keys())
            if absent:
                missing[gid] = absent
        assert not missing, f"Gauges missing required fields: {missing}"

    def test_gauge_ids_are_well_formed(self, gaugehc):
        valid_prefixes = ("GAUGE-", "SYNTH-")
        bad = [gid for gid in gaugehc["hazard_curves"]
               if not gid.startswith(valid_prefixes)]
        assert not bad, f"Gauge IDs not in GAUGE-/SYNTH-xxxx format: {bad[:5]}"

    def test_flood_trigger_ordering(self, gaugehc):
        """alert < warning < severe for every gauge."""
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            a = g.get("flood_alert_m", 0)
            w = g.get("flood_warning_m", 0)
            s = g.get("severe_flood_warning_m", 0)
            if not (a < w < s):
                violations.append((gid, a, w, s))
        assert not violations, f"Flood trigger ordering violated: {violations[:3]}"

    def test_hazard_rates_positive(self, gaugehc):
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            for field in ("annual_hazard_rate_alert", "annual_hazard_rate_warning", "annual_hazard_rate_severe"):
                v = g.get(field, -1)
                if v <= 0:
                    violations.append((gid, field, v))
        assert not violations, f"Non-positive hazard rates found: {violations[:3]}"

    def test_hazard_rate_ordering(self, gaugehc):
        """alert > warning > severe (higher trigger = lower probability)."""
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            ra = g.get("annual_hazard_rate_alert", 0)
            rw = g.get("annual_hazard_rate_warning", 0)
            rs = g.get("annual_hazard_rate_severe", 0)
            if not (ra > rw > rs):
                violations.append((gid, ra, rw, rs))
        assert not violations, f"Hazard rate ordering violated: {violations[:3]}"

    def test_curve_points_present(self, gaugehc):
        missing = [gid for gid, g in gaugehc["hazard_curves"].items()
                   if not g.get("curve_points")]
        assert not missing, f"Gauges with empty curve_points: {missing[:5]}"

    def test_term_structure_present(self, gaugehc):
        missing = [gid for gid, g in gaugehc["hazard_curves"].items()
                   if not g.get("term_structure_alert")]
        assert not missing, f"Gauges missing term_structure_alert: {missing[:5]}"


# ---------------------------------------------------------------------------
# Market state (market_state.json)
# ---------------------------------------------------------------------------

class TestMarketStateData:
    """market_state.json must exist and contain a valid yield curve and hazard term structures."""

    @pytest.fixture(scope="class")
    def ms(self):
        assert MARKET_STATE.exists(), f"market_state.json not found at {MARKET_STATE}"
        return json.loads(MARKET_STATE.read_text())

    def test_file_exists(self):
        assert MARKET_STATE.exists(), f"Missing: {MARKET_STATE}"

    def test_has_required_keys(self, ms):
        missing = MARKET_STATE_REQUIRED_KEYS - set(ms.keys())
        assert not missing, f"market_state.json missing keys: {missing}"

    def test_yield_curve_has_all_tenors(self, ms):
        yc = ms.get("yield_curve", {})
        present = set(str(k) for k in yc.keys())
        missing = YIELD_CURVE_TENORS - present
        assert not missing, f"Yield curve missing tenors: {missing}"

    def test_yield_curve_rates_in_range(self, ms):
        yc = ms.get("yield_curve", {})
        bad = {t: r for t, r in yc.items() if not (0 < r < 1)}
        assert not bad, f"Yield curve rates outside (0,1): {bad}"

    def test_hazard_term_structure_not_empty(self, ms):
        hts = ms.get("hazard_term_structure", {})
        assert hts, "hazard_term_structure is empty"

    def test_hazard_term_structure_has_triggers(self, ms):
        hts = ms.get("hazard_term_structure", {})
        for gid, triggers in hts.items():
            assert "alert" in triggers, f"GAUGE {gid} missing 'alert' in hazard_term_structure"
            break  # spot-check first gauge

    def test_base_rates_not_empty(self, ms):
        br = ms.get("base_rates", {})
        assert br, "base_rates is empty in market_state.json"

    def test_last_updated_present(self, ms):
        assert "last_updated" in ms, "market_state.json missing 'last_updated' field"
