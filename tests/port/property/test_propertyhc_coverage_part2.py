# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Coverage-completion tests for property hazard curve modules (part 2):
  - generator.py: skipped property, progress log, decomposition edge cases
  - loader.py: sequence_gauge enrichment
  - pricing.py: synthetic gauge basis and spreads
"""

import json
from unittest.mock import patch

import pytest

from port.src.property.propertyhc import (
    TENORS,
    PropertyHazardCurveGenerator,
)

from .conftest import write_gauge_hc, write_property_ts


# ===========================================================================
# loader.py lines 50-57 — sequence_gauge enrichment
# ===========================================================================

class TestLoaderSequenceGaugeEnrichment:

    def test_severe_event_count_from_sequence_gauge(self, basic_output_dir):
        """Gauge hazard curves enriched with severe_event_count from sequence_gauge/."""
        output_dir, pts_dir = basic_output_dir

        # Create sequence_gauge directory with gauge files
        sg_dir = output_dir / 'sequence_gauge'
        sg_dir.mkdir()

        gauge1_data = {
            'sequences': [
                {'storm_id': 'S1', 'severe': True},
                {'storm_id': 'S2', 'severe': False},
                {'storm_id': 'S3', 'severe': True},
                {'storm_id': 'S4', 'severe': True},
            ]
        }
        (sg_dir / 'GAUGE-001.json').write_text(json.dumps(gauge1_data))

        gauge2_data = {
            'sequences': [
                {'storm_id': 'S1', 'severe': False},
                {'storm_id': 'S2', 'severe': True},
            ]
        }
        (sg_dir / 'GAUGE-002.json').write_text(json.dumps(gauge2_data))

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        hazard_curves, _ = gen._load_gauge_hazard_curves()

        assert hazard_curves['GAUGE-001']['severe_event_count'] == 3
        assert hazard_curves['GAUGE-002']['severe_event_count'] == 1

    def test_missing_sequence_gauge_file_skipped(self, basic_output_dir):
        """Gauge without a matching sequence_gauge file is not enriched."""
        output_dir, pts_dir = basic_output_dir

        sg_dir = output_dir / 'sequence_gauge'
        sg_dir.mkdir()
        # Only write for GAUGE-001, not GAUGE-002
        (sg_dir / 'GAUGE-001.json').write_text(json.dumps({
            'sequences': [{'storm_id': 'S1', 'severe': True}]
        }))

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        hazard_curves, _ = gen._load_gauge_hazard_curves()

        assert hazard_curves['GAUGE-001']['severe_event_count'] == 1
        assert 'severe_event_count' not in hazard_curves['GAUGE-002']


# ===========================================================================
# pricing.py lines 113-115 — synthetic gauge summary (avg_basis, avg_transmission)
# ===========================================================================

class TestPricingSyntheticGaugeSummary:

    def _make_synth_setup(self, output_dir, pts_dir):
        """Set up gauge hazard + property with SYNTH- nearest gauge."""
        # Write gaugehc with a SYNTH- gauge entry
        gauge_data = {
            "metadata": {"catchment_id": "test", "num_storms": 100},
            "hazard_curves": {
                "SYNTH-001": {
                    "annual_hazard_rate_alert": 0.05,
                    "annual_hazard_rate_warning": 0.02,
                    "annual_hazard_rate_severe": 0.01,
                    "annual_flood_prob_severe": 0.1,
                },
            },
        }
        (output_dir / "gaugehc.json").write_text(json.dumps(gauge_data))

        # Property with SYNTH- nearest gauge
        write_property_ts(
            pts_dir, "PROP-synth", n_floods=5,
            nearest_gauges=[
                {"gauge_id": "SYNTH-001", "distance_m": 500,
                 "gauge_elevation_m": 3.0},
            ],
        )

    def test_synth_gauge_sets_avg_basis(self, basic_output_dir):
        """When nearest gauge is SYNTH-, avg_basis comes from synth basis."""
        output_dir, pts_dir = basic_output_dir
        self._make_synth_setup(output_dir, pts_dir)

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, num_storms = gen._load_gauge_hazard_curves()
        prop_file = pts_dir / "PROP-synth.json"
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=num_storms)

        # synth_nb is found, so summary uses its basis
        assert result['summary']['avg_basis_bps'] is not None
        assert isinstance(result['summary']['avg_basis_bps'], float)

    def test_synth_gauge_sets_transmission_rate(self, basic_output_dir):
        """When nearest gauge is SYNTH-, transmission rate from synth gauge."""
        output_dir, pts_dir = basic_output_dir
        self._make_synth_setup(output_dir, pts_dir)

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, num_storms = gen._load_gauge_hazard_curves()
        prop_file = pts_dir / "PROP-synth.json"
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=num_storms)

        assert result['summary']['flood_transmission_rate'] is not None


# ===========================================================================
# pricing.py lines 131-136 — synthetic gauge idw_gauge_spreads
# ===========================================================================

class TestPricingSyntheticGaugeSpreads:

    def test_synth_gauge_produces_idw_severe_spreads(self, basic_output_dir):
        """When SYNTH- gauge exists, idw_gauge_spreads['severe'] is set from synth basis."""
        output_dir, pts_dir = basic_output_dir

        gauge_data = {
            "metadata": {"catchment_id": "test", "num_storms": 100},
            "hazard_curves": {
                "SYNTH-001": {
                    "annual_hazard_rate_alert": 0.05,
                    "annual_hazard_rate_warning": 0.02,
                    "annual_hazard_rate_severe": 0.01,
                    "annual_flood_prob_severe": 0.1,
                },
            },
        }
        (output_dir / "gaugehc.json").write_text(json.dumps(gauge_data))

        write_property_ts(
            pts_dir, "PROP-synthspread", n_floods=5,
            nearest_gauges=[
                {"gauge_id": "SYNTH-001", "distance_m": 500,
                 "gauge_elevation_m": 3.0},
            ],
        )

        gen = PropertyHazardCurveGenerator(output_dir, verbose=False)
        gauge_hazard, num_storms = gen._load_gauge_hazard_curves()
        prop_file = pts_dir / "PROP-synthspread.json"
        result = gen._process_property(prop_file, gauge_hazard, None, num_storms=num_storms)

        idw = result.get('idw_gauge_spreads', {})
        assert 'severe' in idw
        assert len(idw['severe']) == len(TENORS)
        # Each value should be spread_bps + basis
        assert all(isinstance(v, float) for v in idw['severe'])
