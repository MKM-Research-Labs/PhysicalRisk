# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for routes/propertyts/financial.py — gauge / property / sequence loaders.

Split from test_financial_coverage_extra.py.  Shared helpers in
``_financial_coverage_helpers.py``.
"""

import json

import pytest

from tests.routes.propertyts._helpers import PROP_ID, SEQ_ID, STORM_ID
from tests.routes.propertyts._financial_coverage_helpers import (
    _build_client,
    _make_mortgage,
    _make_prop_details,
    _make_prop_flood,
    _make_prs_trade,
)


class TestLoadGaugeElevations:

    def test_blotter_works_without_gauge_or_gaugehc(
            self, tmp_path, monkeypatch):
        """When both gauge.json and gaugehc.json are missing, elevations
        default to 0; the blotter still returns the property."""
        from config import config

        (tmp_path / 'property.json').write_text(
            json.dumps(_make_prop_details(gauge='GAUGE-XYZ')))
        (tmp_path / 'mortgage.json').write_text(json.dumps(_make_mortgage()))
        (tmp_path / 'propertyts').mkdir()

        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        monkeypatch.setattr(config, 'get_input_path',
                            lambda f: tmp_path / f)
        monkeypatch.setattr(config, 'get_gaugets_dir',
                            lambda: tmp_path / 'gaugets')

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        r = client.get('/api/v1/propertyts/blotter')
        assert r.status_code == 200
        props = r.get_json()['properties']
        assert len(props) == 1
        # ground=6.0, gauge_elev fallback=0 → relative=6.0 + floor=3.2 = 9.2
        assert props[0]['elevation_m'] == pytest.approx(9.2, abs=0.01)

    def test_gaugehc_fallback_when_gauge_absent_from_gauge_json(
            self, tmp_path, monkeypatch):
        """Gauge is only in gaugehc.json → elevation sourced from there."""
        # gauge.json present but empty
        gauge_json = {'flood_gauges': []}
        gaugehc_json = {
            'hazard_curves': {
                'GAUGE-HC-ONLY': {
                    'gauge_name': 'HC Only',
                    'elevation_m': 12.0,
                    'flood_alert_m': 4.0,
                    'flood_warning_m': 4.5,
                    'severe_flood_warning_m': 5.0,
                    'latitude': 51.5,
                    'longitude': -0.1,
                }
            }
        }
        property_json = _make_prop_details(gauge='GAUGE-HC-ONLY',
                                           ground=14.0, floor=0.5)
        client = _build_client(
            tmp_path, monkeypatch,
            property_json=property_json,
            mortgage_json=_make_mortgage(),
            gauge_json=gauge_json,
            gaugehc_json=gaugehc_json,
        )
        r = client.get('/api/v1/propertyts/blotter')
        assert r.status_code == 200
        props = r.get_json()['properties']
        # rel = max(0, 14.0 - 12.0) + 0.5 = 2.5
        assert props[0]['elevation_m'] == pytest.approx(2.5, abs=0.01)

    def test_corrupt_gaugehc_json_is_tolerated(self, tmp_path, monkeypatch):
        """Broken gaugehc.json logs a warning but the endpoint still works."""
        gauge_json = {'flood_gauges': [{'FloodGauge': {
            'Header': {'GaugeID': 'GAUGE-X'},
            'Location': {'GaugeElevation': 5.0},
        }}]}
        property_json = _make_prop_details(gauge='GAUGE-X', ground=8.0)
        client = _build_client(
            tmp_path, monkeypatch,
            property_json=property_json,
            mortgage_json=_make_mortgage(),
            gauge_json=gauge_json,
            gaugehc_json='{not valid',  # corrupt
        )
        r = client.get('/api/v1/propertyts/blotter')
        assert r.status_code == 200
        props = r.get_json()['properties']
        # rel = max(0, 8 - 5) + 3.2 = 6.2
        assert props[0]['elevation_m'] == pytest.approx(6.2, abs=0.01)


# ===========================================================================
# _load_property_details exception path
# ===========================================================================

class TestLoadPropertyDetailsException:
    """When property.json is missing, blotter returns empty property list."""

    def test_blotter_with_no_property_json(self, tmp_path, monkeypatch):
        from config import config

        (tmp_path / 'propertyts').mkdir()
        (tmp_path / 'mortgage.json').write_text(json.dumps({'mortgages': []}))

        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        monkeypatch.setattr(config, 'get_input_path',
                            lambda f: tmp_path / f)
        monkeypatch.setattr(config, 'get_gaugets_dir',
                            lambda: tmp_path / 'gaugets')

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        r = client.get('/api/v1/propertyts/blotter')
        assert r.status_code == 200
        assert r.get_json()['properties'] == []
        assert r.get_json()['summary']['num_properties'] == 0


# ===========================================================================
# _enrich_with_prs — LTV=999 branch (100% damage → post value 0)
# ===========================================================================

class TestEnrichWithPrsLtv999:
    """When damage_ratio=1.0 post-damage value is 0, post_damage_ltv=999."""

    def test_total_loss_gives_ltv_999(self, tmp_path, monkeypatch):
        pf = _make_prop_flood(depth=5.0, damage=1.0)
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        prop = r.get_json()['properties'][0]
        assert prop['post_damage_value'] == 0
        assert prop['post_damage_ltv'] == 999
        assert prop['negative_equity'] is True


# ===========================================================================
# Basis endpoint edge cases
# ===========================================================================


# ===========================================================================
# Sequence endpoint — legacy sequence_id field fallback
# ===========================================================================

class TestSequenceLegacySequenceIdFallback:
    """If a flood event carries a legacy `sequence_id` field, the sequence
    endpoint should still match it even when storm_id differs."""

    def test_legacy_sequence_id_field_matches(self, tmp_path, monkeypatch):
        pf = {
            'property_id': PROP_ID,
            'nearest_gauges': [
                {'gauge_id': 'SYNTH-001'},
                {'gauge_id': 'GAUGE-001'},
            ],
            'flood_events': [{
                'storm_id': 'PULSE-XYZ',       # different from sequence
                'sequence_id': SEQ_ID,         # legacy field
                'flooded': True,
                'exceeded_severe': True,
                'flood_depth_m': 0.6,
                'damage_ratio': 0.12,
            }],
        }
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[],
        )
        r = client.get(
            f'/api/v1/propertyts/sequence/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        props = r.get_json()['properties']
        assert len(props) == 1
        assert props[0]['worst_storm_id'] == 'PULSE-XYZ'
        assert props[0]['flood_depth_m'] == pytest.approx(0.6, abs=1e-6)
