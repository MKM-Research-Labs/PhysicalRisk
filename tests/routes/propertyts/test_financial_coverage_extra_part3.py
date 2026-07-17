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

"""Coverage tests for routes/propertyts/financial.py — basis endpoint edge cases.

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


class TestBasisEdgeCases:

    def test_basis_options_returns_ok(self, tmp_path, monkeypatch):
        from config import config

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
        r = client.options(f'/api/v1/propertyts/{SEQ_ID}/basis')
        assert r.status_code == 200
        assert r.get_json()['status'] == 'ok'

    def test_basis_no_pts_dir_returns_404(self, tmp_path, monkeypatch):
        from config import config

        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        monkeypatch.setattr(config, 'get_input_path',
                            lambda f: tmp_path / f)
        monkeypatch.setattr(config, 'get_gaugets_dir',
                            lambda: tmp_path / 'gaugets')

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        assert r.status_code == 404
        assert r.get_json()['status'] == 'error'

    def test_basis_property_without_nearest_gauges_is_skipped(
            self, tmp_path, monkeypatch):
        """Property with empty nearest_gauges is not accumulated."""
        pf = _make_prop_flood(nearest=[])
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        assert r.status_code == 200
        assert r.get_json()['gauges'] == []

    def test_basis_property_with_empty_gauge_id_is_skipped(
            self, tmp_path, monkeypatch):
        """Synthetic gauge with empty gauge_id → skipped."""
        pf = _make_prop_flood(nearest=[
            {'gauge_id': '', 'distance_m': 10}
        ])
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        assert r.status_code == 200
        assert r.get_json()['gauges'] == []

    def test_basis_threshold_clean_no_flood_event(
            self, tmp_path, monkeypatch):
        """No flood event for this storm → peak_wse=0, threshold='clean'."""
        pf = {
            'property_id': PROP_ID,
            'nearest_gauges': [
                {'gauge_id': 'SYNTH-CLEAN'},
                {'gauge_id': 'GAUGE-REAL'},
            ],
            # Flood event exists but for a different storm
            'flood_events': [{
                'storm_id': 'OTHER-STORM',
                'flooded': False,
                'flood_depth_m': 0.0,
            }],
        }
        gaugehc = {'hazard_curves': {
            'SYNTH-CLEAN': {
                'gauge_name': 'Clean Synth',
                'flood_alert_m': 4.0,
                'flood_warning_m': 4.5,
                'severe_flood_warning_m': 5.0,
                'elevation_m': 3.0,
            }
        }}
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            gaugehc_json=gaugehc,
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        data = r.get_json()
        g = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-CLEAN'][0]
        assert g['threshold'] == 'clean'
        assert g['properties_flooded'] == 0
        assert g['transmission_pct'] == 0

    def test_basis_threshold_alert_branch(self, tmp_path, monkeypatch):
        """peak_wse between alert and warning → threshold='alert'."""
        pf = {
            'property_id': PROP_ID,
            'nearest_gauges': [
                {'gauge_id': 'SYNTH-ALERT'},
                {'gauge_id': 'GAUGE-REAL'},
            ],
            'flood_events': [{
                'storm_id': SEQ_ID,
                'flooded': False,
                'exceeded_severe': False,
                'flood_depth_m': 0.0,
                'interpolated_wse_m': 4.1,  # >= alert(4.0), < warning(4.5)
                'damage_ratio': 0.0,
            }],
        }
        gaugehc = {'hazard_curves': {
            'SYNTH-ALERT': {
                'gauge_name': 'Alert Synth',
                'flood_alert_m': 4.0,
                'flood_warning_m': 4.5,
                'severe_flood_warning_m': 5.0,
                'elevation_m': 3.0,
            }
        }}
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            gaugehc_json=gaugehc,
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        data = r.get_json()
        g = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-ALERT'][0]
        assert g['threshold'] == 'alert'

    def test_basis_threshold_warning_branch(self, tmp_path, monkeypatch):
        """peak_wse between warning and severe → threshold='warning'."""
        pf = {
            'property_id': PROP_ID,
            'nearest_gauges': [
                {'gauge_id': 'SYNTH-WARN'},
                {'gauge_id': 'GAUGE-REAL'},
            ],
            'flood_events': [{
                'storm_id': SEQ_ID,
                'flooded': False,
                'exceeded_severe': False,
                'flood_depth_m': 0.0,
                'interpolated_wse_m': 4.7,  # >= warning(4.5)
                'damage_ratio': 0.0,
            }],
        }
        gaugehc = {'hazard_curves': {
            'SYNTH-WARN': {
                'gauge_name': 'Warn Synth',
                'flood_alert_m': 4.0,
                'flood_warning_m': 4.5,
                'severe_flood_warning_m': 5.0,
                'elevation_m': 3.0,
            }
        }}
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            gaugehc_json=gaugehc,
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        data = r.get_json()
        g = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-WARN'][0]
        assert g['threshold'] == 'warning'

    def test_basis_corrupt_prop_file_is_skipped(
            self, tmp_path, monkeypatch):
        """Corrupt PROP-*.json is tolerated; the valid one still appears."""
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            extra_prop_files={'PROP-BROKEN.json': '{not valid'},
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        assert r.status_code == 200
        # Should only have entry for the valid SYNTH-001 gauge
        data = r.get_json()
        assert any(g['gauge_id'] == 'SYNTH-001' for g in data['gauges'])

    def test_basis_storm_file_missing_keeps_zero_real_peak(
            self, tmp_path, monkeypatch):
        """No stress_storms/<id>.json file → real_gauge_peak_m defaults to 0."""
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            gaugehc_json={'hazard_curves': {
                'SYNTH-001': {
                    'gauge_name': 'Synth One',
                    'flood_alert_m': 4.0,
                    'flood_warning_m': 4.5,
                    'severe_flood_warning_m': 5.0,
                    'elevation_m': 3.0,
                }
            }},
            # storm_file=None → no stress_storms/<id>.json
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        data = r.get_json()
        g = [g for g in data['gauges'] if g['gauge_id'] == 'SYNTH-001'][0]
        assert g['real_gauge_peak_m'] == 0
        assert g['real_gauge_severe'] is False

    def test_basis_summary_fields_present(self, tmp_path, monkeypatch):
        """Summary section has all expected keys."""
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/basis')
        s = r.get_json()['summary']
        for key in ('num_synthetic_gauges', 'gauges_severe',
                    'gauges_with_flooding', 'gauges_basis_only',
                    'total_properties', 'total_flooded',
                    'portfolio_transmission_pct'):
            assert key in s


