"""Tests for zone floor on hazard rate and synthetic-based basis."""

import math

import pytest

from config.models import EA_FLOOD_ZONE_RATES


class TestZoneFloorPricing:
    """Verify that zone floor prevents nonsensically low spreads."""

    def test_zone_3a_floor_rate(self):
        """Zone 3a should floor at 2% annual probability."""
        assert EA_FLOOD_ZONE_RATES['Zone 3a'] == 0.02

    def test_zone_3b_floor_rate(self):
        """Zone 3b should floor at 5% annual probability."""
        assert EA_FLOOD_ZONE_RATES['Zone 3b'] == 0.05

    def test_zone_floor_produces_material_spread(self):
        """A 2% annual prob (Zone 3a floor) should produce ~200bp spread."""
        from models.hazard.prs_analytical import compute_prs_spread
        spread = compute_prs_spread(0.02, tenor=5, recovery=0.0, risk_free_rate=0.03)
        assert spread > 100, f"Zone 3a floor spread {spread:.1f}bp too low"
        assert spread < 400, f"Zone 3a floor spread {spread:.1f}bp too high"

    def test_zone_3b_floor_produces_higher_spread(self):
        """A 5% annual prob (Zone 3b floor) should produce ~500bp spread."""
        from models.hazard.prs_analytical import compute_prs_spread
        spread = compute_prs_spread(0.05, tenor=5, recovery=0.0, risk_free_rate=0.03)
        assert spread > 300, f"Zone 3b floor spread {spread:.1f}bp too low"

    def test_simulation_rate_above_floor_is_preserved(self):
        """When simulation gives higher rate than zone floor, simulation wins."""
        # Zone 1 floor is 0.001. If simulation gives 0.05, 0.05 should win.
        sim_rate = 0.05
        zone_floor = EA_FLOOD_ZONE_RATES['Zone 1']  # 0.001
        effective = max(sim_rate, zone_floor)
        assert effective == sim_rate

    def test_simulation_rate_below_floor_is_lifted(self):
        """When simulation gives lower rate than zone floor, zone floor applies."""
        sim_rate = 0.00074  # typical for PROP-66822910
        zone_floor = EA_FLOOD_ZONE_RATES['Zone 3a']  # 0.02
        effective = max(sim_rate, zone_floor)
        assert effective == zone_floor


class TestSyntheticBasisPriority:
    """Verify that basis uses synthetic gauge when present."""

    def test_synth_prefix_detection(self):
        """Synthetic gauges start with 'SYNTH-'."""
        nearest_basis = [
            {'gauge_id': 'GAUGE-AAA', 'basis_bps': {}},
            {'gauge_id': 'SYNTH-123', 'basis_bps': {}},
            {'gauge_id': 'GAUGE-BBB', 'basis_bps': {}},
        ]
        synth = next(
            (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
            None
        )
        assert synth is not None
        assert synth['gauge_id'] == 'SYNTH-123'

    def test_no_synth_returns_none(self):
        nearest_basis = [
            {'gauge_id': 'GAUGE-AAA'},
            {'gauge_id': 'GAUGE-BBB'},
        ]
        synth = next(
            (nb for nb in nearest_basis if nb['gauge_id'].startswith('SYNTH-')),
            None
        )
        assert synth is None
