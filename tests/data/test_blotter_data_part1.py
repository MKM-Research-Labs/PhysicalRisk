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

"""
Data availability tests — Blotter (part 1).

Gauge hazard curves (gaugehc.json), market state (market_state.json).
"""

import json
import pathlib

import pytest

from tests._dataset import full_dataset_only

from config import config as _config

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

    def test_every_gauge_has_a_hazard_curve(self, gaugehc):
        """Hazard-curve coverage must be complete for the generated gauge set.

        Was ``count >= 40`` guarded by a skip when ``count < 40`` — so the
        assertion was unreachable when false and the check could not fail. The
        magic 40 also assumed the full portfolio; a smaller generated set is a
        legitimate dataset, not a broken one.

        Comparing against the gauges actually generated is both scale-free and
        stronger: a missing curve now fails at any size.
        """
        gauge_path = pathlib.Path(_config.get_input_dir()) / "gauge.json"
        if not gauge_path.exists():
            pytest.skip(f"gauge.json not generated at {gauge_path}")

        gauges = json.loads(gauge_path.read_text()).get("gauges", [])
        expected = {
            (g.get("GaugeHeader", {}).get("Header", {}).get("GaugeID")
             or g.get("gauge_id"))
            for g in gauges
        }
        expected.discard(None)
        if not expected:
            pytest.skip("gauge.json has no gauges")

        missing = expected - set(gaugehc["hazard_curves"])
        assert not missing, (
            f"{len(missing)} of {len(expected)} gauges have no hazard curve: "
            f"{sorted(missing)[:5]}"
        )

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

    _RATE_FIELDS = ("annual_hazard_rate_alert",
                    "annual_hazard_rate_warning",
                    "annual_hazard_rate_severe")

    def test_hazard_rates_present_and_non_negative(self, gaugehc):
        """Every trigger carries a rate, and no rate is negative.

        Structural, so it holds at any portfolio size. A *zero* severe rate is
        the expected answer on a small sample — 100 simulated sequences need
        not contain a severe event — so strict positivity is asserted
        separately against the full portfolio.
        """
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            for field in self._RATE_FIELDS:
                v = g.get(field)
                if v is None or v < 0:
                    violations.append((gid, field, v))
        assert not violations, f"Missing or negative hazard rates: {violations[:3]}"

    @full_dataset_only
    def test_hazard_rates_positive(self, gaugehc):
        """At full scale every trigger must actually have been observed."""
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            for field in self._RATE_FIELDS:
                v = g.get(field, -1)
                if v <= 0:
                    violations.append((gid, field, v))
        assert not violations, f"Non-positive hazard rates found: {violations[:3]}"

    def test_hazard_rate_ordering(self, gaugehc):
        """alert >= warning >= severe (higher trigger = lower probability).

        Non-strict: tiers that the sample never reached are all zero, which is
        correct rather than a violation. The strict form runs at full scale.
        """
        violations = []
        for gid, g in gaugehc["hazard_curves"].items():
            ra = g.get("annual_hazard_rate_alert", 0)
            rw = g.get("annual_hazard_rate_warning", 0)
            rs = g.get("annual_hazard_rate_severe", 0)
            if not (ra >= rw >= rs):
                violations.append((gid, ra, rw, rs))
        assert not violations, f"Hazard rate ordering violated: {violations[:3]}"

    @full_dataset_only
    def test_hazard_rate_ordering_strict(self, gaugehc):
        """alert > warning > severe, with every tier genuinely distinct."""
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
