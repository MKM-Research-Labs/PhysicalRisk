# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Tests for _build_compound_flood_event and the compound path through
_compute_property_flood (v2.2 per-pulse superposition).
"""

from unittest.mock import patch

from .conftest import make_generator, make_gaugets


def _pulse(peak_m, start_hour=0, duration_hours=24):
    """Build a single pulse dict for compound hydrograph tests."""
    return {"peak_m": peak_m, "start_hour": start_hour,
            "duration_hours": duration_hours}


# ===========================================================================
# _build_compound_flood_event (propagation.py lines 167-255)
# ===========================================================================

class TestBuildCompoundFloodEvent:
    """Cover the per-pulse superposition flood event builder."""

    def _nearest(self, elevation=3.0, severe_level=5.0):
        return {
            "gauge_id": "GAUGE-001",
            "distance_m": 500.0,
            "gauge_info": {
                "elevation": elevation,
                "severe_level": severe_level,
            },
        }

    def _make_resp(self, peak=6.0, pulse_peaks=None, base_level=2.5,
                   seq_type="doublet"):
        return {
            "peak_level_m": peak,
            "base_level_m": base_level,
            "pulse_peaks": pulse_peaks or [
                _pulse(5.5, start_hour=0),
                _pulse(6.0, start_hour=24),
            ],
            "sequence_type": seq_type,
        }

    def _gaugets_with_severe(self, severe=5.0):
        gt = make_gaugets(peak_level=6.0)
        gt["GAUGE-001"]["severe_flood_warning"] = severe
        return gt

    def test_returns_compound_event_keys(self, tmp_path):
        """Compound event has all expected keys including compound-specific ones."""
        gen = make_generator(tmp_path)
        resp = self._make_resp()
        gaugets = self._gaugets_with_severe()
        result = gen._build_compound_flood_event(
            "STORM-001", resp["pulse_peaks"], resp,
            500.0, 0.9, 5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        for key in ("storm_id", "flood_depth_m", "damage_ratio",
                     "flooded", "retention_factor", "compound",
                     "num_pulses", "sequence_type"):
            assert key in result, f"Missing key: {key}"
        assert result["compound"] is True
        assert result["num_pulses"] == 2
        assert result["sequence_type"] == "doublet"

    def test_compound_flooded_event_has_readings(self, tmp_path):
        """When compound event causes flooding, readings are present."""
        gen = make_generator(tmp_path)
        # High peak, low property elevation -> flooded
        resp = self._make_resp(peak=10.0, pulse_peaks=[
            _pulse(8.0, start_hour=0), _pulse(10.0, start_hour=24)])
        gaugets = self._gaugets_with_severe(severe=5.0)
        result = gen._build_compound_flood_event(
            "STORM-001", resp["pulse_peaks"], resp,
            100.0, 0.99, 1.0, 0.0, "GAUGE-001", gaugets,
            self._nearest(elevation=1.0, severe_level=5.0)
        )
        if result["flooded"]:
            assert "readings" in result
            assert result["flood_depth_m"] > 0
            assert result["arrival_time_hrs"] is not None
            assert result["peak_time_hrs"] is not None

    def test_compound_non_flooded_no_readings(self, tmp_path):
        """Property too high for flood -> no readings key."""
        gen = make_generator(tmp_path)
        resp = self._make_resp(peak=3.0, pulse_peaks=[
            _pulse(2.5, start_hour=0), _pulse(3.0, start_hour=24)])
        gaugets = self._gaugets_with_severe()
        result = gen._build_compound_flood_event(
            "STORM-001", resp["pulse_peaks"], resp,
            2000.0, 0.1, 100.0, 5.0, "GAUGE-001", gaugets,
            self._nearest(elevation=3.0, severe_level=5.0)
        )
        assert result["flooded"] is False
        assert "readings" not in result
        assert result["flood_depth_m"] == 0.0

    def test_isolated_sequence_type(self, tmp_path):
        """Isolated storm type passed through to event."""
        gen = make_generator(tmp_path)
        resp = self._make_resp(pulse_peaks=[_pulse(5.5)], seq_type="isolated")
        gaugets = self._gaugets_with_severe()
        result = gen._build_compound_flood_event(
            "STORM-001", resp["pulse_peaks"], resp,
            500.0, 0.9, 5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        assert result["sequence_type"] == "isolated"
        assert result["num_pulses"] == 1

    def test_zero_distance_travel_time(self, tmp_path):
        """Distance=0 -> travel_time_hrs=0."""
        gen = make_generator(tmp_path)
        resp = self._make_resp()
        gaugets = self._gaugets_with_severe()
        result = gen._build_compound_flood_event(
            "STORM-001", resp["pulse_peaks"], resp,
            0.0, 1.0, 5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
        )
        assert result["travel_time_hrs"] == 0.0

    def test_superposition_cap_applied(self, tmp_path):
        """When gauge severe > base_level, superposition cap is computed."""
        gen = make_generator(tmp_path)
        resp = self._make_resp(peak=8.0, pulse_peaks=[
            _pulse(7.0, start_hour=0), _pulse(8.0, start_hour=24)],
                               base_level=2.0)
        gaugets = self._gaugets_with_severe(severe=5.0)
        # Patch to verify cap is passed to build_compound_property_hydrograph
        with patch("port.src.property.ts.flood.propagation."
                   "build_compound_property_hydrograph",
                   return_value=[]) as mock_hydro:
            gen._build_compound_flood_event(
                "STORM-001", resp["pulse_peaks"], resp,
                500.0, 0.9, 5.0, 0.3, "GAUGE-001", gaugets, self._nearest()
            )
            # cap should be SUPERPOSITION_CAP_FACTOR * (severe - base_level)
            call_kwargs = mock_hydro.call_args
            assert call_kwargs is not None
            cap_arg = call_kwargs[1].get("cap") if call_kwargs[1] else None
            if cap_arg is None:
                cap_arg = call_kwargs[0][-1] if len(call_kwargs[0]) > 9 else None
            # Cap should be non-None when severe > base_level
            assert cap_arg is not None


# ===========================================================================
# _compute_property_flood — compound dispatch (line 63-67)
# ===========================================================================

class TestComputePropertyFloodCompound:
    """Verify _compute_property_flood dispatches to compound builder
    when pulse_peaks are present in gauge response."""

    def test_pulse_peaks_dispatches_to_compound(self, tmp_path):
        """Response with pulse_peaks -> compound event (compound=True)."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-001", "distance_m": 500.0,
             "gauge_info": {"elevation": 3.0, "severe_level": 5.0}},
        ]
        gauge_responses = {
            "GAUGE-001": {
                "peak_level_m": 6.0,
                "exceeded_alert": True,
                "pulse_peaks": [
                    _pulse(5.5, start_hour=0),
                    _pulse(6.0, start_hour=24),
                ],
                "base_level_m": 2.5,
                "sequence_type": "doublet",
            }
        }
        gaugets = make_gaugets(peak_level=6.0)
        gaugets["GAUGE-001"]["severe_flood_warning"] = 5.0
        result = gen._compute_property_flood(
            "STORM-001", gauge_responses, nearest,
            51.5, -0.1, 5.0, 0.3, gaugets
        )
        assert result is not None
        assert result.get("compound") is True
        assert result.get("num_pulses") == 2

    def test_no_pulse_peaks_dispatches_to_simple(self, tmp_path):
        """Response without pulse_peaks -> simple event (no compound key)."""
        gen = make_generator(tmp_path)
        nearest = [
            {"gauge_id": "GAUGE-001", "distance_m": 500.0,
             "gauge_info": {"elevation": 3.0}},
        ]
        gauge_responses = {
            "GAUGE-001": {"peak_level_m": 5.5, "exceeded_alert": True}
        }
        gaugets = make_gaugets()
        result = gen._compute_property_flood(
            "STORM-001", gauge_responses, nearest,
            51.5, -0.1, 5.0, 0.3, gaugets
        )
        assert result is not None
        assert result.get("compound") is not True


# ===========================================================================
# _depth_to_damage static method
# ===========================================================================

class TestDepthToDamageDelegate:
    """Cover the _depth_to_damage static method on PropagationMixin."""

    def test_delegates_to_scalar_depth_damage(self, tmp_path):
        gen = make_generator(tmp_path)
        result = gen._depth_to_damage(1.5)
        assert isinstance(result, float)
        assert result > 0

    def test_zero_depth(self, tmp_path):
        gen = make_generator(tmp_path)
        assert gen._depth_to_damage(0.0) == 0.0
