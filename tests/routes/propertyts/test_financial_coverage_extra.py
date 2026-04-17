# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Additional coverage tests for routes/propertyts/financial.py.

Targets branches not exercised by test_financial_coverage.py or
test_financial_derivatives.py:

  - _match_prs_to_properties: gauge-based matching + dedup when a
    trade matches both directly (property_id) and via gauge_id.
  - _load_all_prs_trades: no prs dir, corrupt PRS file, empty GaugeBasket.
  - _load_gauge_elevations: missing gauge.json and missing gaugehc.json.
  - _load_gauge_elevations: gaugehc fallback when a gauge is absent
    from gauge.json.
  - _load_property_details: missing property.json (exception path).
  - _enrich_with_prs: post_damage_value <= 0 → LTV = 999 branch.
  - Basis endpoint: OPTIONS, no pts_dir, threshold=warning/alert/clean,
    property without nearest_gauges, property with empty synth_id,
    corrupt PROP file, storm file missing / no gauge_responses.
  - Sequence endpoint: legacy `sequence_id` field match when storm_id
    does not equal the sequence id.
"""

import json

import pytest

from tests.routes.propertyts._helpers import PROP_ID, SEQ_ID, STORM_ID


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_prs_trade(swap_id, gauge_id, property_id, notional=250_000,
                    trigger='severe', trade_type='PropertyPRS'):
    return {
        'PhysicalSwap': {
            'Header': {
                'SwapID': swap_id,
                'TradeType': trade_type,
                'CounterPartyName': 'Test REIT',
            },
            'LegData': {'Notional': notional, 'Payer': True},
            'Pricing': {'SpreadBps': 120.0, 'TriggerLevel': trigger},
            'GaugeSet': {'GaugeBasket': (
                [{'GaugeID': gauge_id}] if gauge_id else []
            )},
            'PropertySet': {'PropertyID': property_id} if property_id else {},
        }
    }


def _make_prop_details(property_id=PROP_ID, value=400_000,
                       ground=6.0, floor=3.2, gauge='GAUGE-001'):
    return {'properties': [{'PropertyHeader': {
        'Header': {'PropertyID': property_id},
        'Location': {
            'BuildingNumber': '1',
            'StreetName': 'High St',
            'Postcode': 'SW1A 1AA',
            'LatitudeDegrees': 51.5,
            'LongitudeDegrees': -0.12,
        },
        'Valuation': {'PropertyValue': value},
        'Construction': {'FloorLevelMeters': floor},
        'RiskAssessment': {
            'GroundLevelMeters': ground,
            'RiverDistanceMeters': 500,
            'EAFloodZone': 'Zone 3',
        },
        'ReferenceGauges': [gauge] if gauge else [],
    }}]}


def _make_mortgage(property_id=PROP_ID, outstanding=280_000,
                   ltv=70.0, term=240):
    return {'mortgages': [{'Mortgage': {
        'Header': {'MortgageID': 'MORT-001', 'PropertyID': property_id},
        'CurrentStatus': {
            'OutstandingBalance': outstanding,
            'CurrentLTV': ltv,
            'RemainingTerm': term,
        },
    }}]}


def _make_prop_flood(property_id=PROP_ID, storm_id=SEQ_ID,
                     depth=0.5, damage=0.1, nearest=None,
                     interpolated_wse=5.5, retention=0.9,
                     exceeded_severe=True, flooded=True):
    return {
        'property_id': property_id,
        'nearest_gauges': nearest if nearest is not None else [
            {'gauge_id': 'SYNTH-001', 'distance_m': 200},
            {'gauge_id': 'GAUGE-001', 'distance_m': 500},
        ],
        'flood_events': [{
            'storm_id': storm_id,
            'flooded': flooded,
            'exceeded_severe': exceeded_severe,
            'flood_depth_m': depth,
            'damage_ratio': damage,
            'interpolated_wse_m': interpolated_wse,
            'retention_factor': retention,
        }],
    }


def _build_client(tmp_path, monkeypatch, *,
                  prop_flood=None, property_json=None,
                  mortgage_json=None, gauge_json=None,
                  gaugehc_json=None, prs_trades=None,
                  storm_file=None, include_prs_dir=True,
                  extra_prop_files=None):
    """Create a full test client with flexible fixture data."""
    from config import config

    pts_dir = tmp_path / 'propertyts'
    pts_dir.mkdir()
    gaugets_dir = tmp_path / 'gaugets'
    gaugets_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    prs_dir = output_dir / 'prs'
    if include_prs_dir:
        prs_dir.mkdir()

    if prop_flood is not None:
        (pts_dir / f"{prop_flood['property_id']}.json").write_text(
            json.dumps(prop_flood))
    for fname, data in (extra_prop_files or {}).items():
        target = pts_dir / fname
        if isinstance(data, str):
            target.write_text(data)
        else:
            target.write_text(json.dumps(data))

    if property_json is not None:
        (tmp_path / 'property.json').write_text(json.dumps(property_json))
    if mortgage_json is not None:
        (tmp_path / 'mortgage.json').write_text(json.dumps(mortgage_json))
    if gauge_json is not None:
        (tmp_path / 'gauge.json').write_text(json.dumps(gauge_json))
    if gaugehc_json is not None:
        if isinstance(gaugehc_json, str):
            (tmp_path / 'gaugehc.json').write_text(gaugehc_json)
        else:
            (tmp_path / 'gaugehc.json').write_text(json.dumps(gaugehc_json))

    if include_prs_dir:
        for i, t in enumerate(prs_trades or []):
            (prs_dir / f'PRS-{i:03d}.json').write_text(json.dumps(t))

    ss_dir = tmp_path / 'stress_storms'
    ss_dir.mkdir()
    if storm_file is not None:
        (ss_dir / f'{SEQ_ID}.json').write_text(json.dumps(storm_file))

    monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
    monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
    monkeypatch.setattr(config, 'get_input_path',
                        lambda fname: tmp_path / fname)
    monkeypatch.setattr(
        config, 'get_reports_dir',
        lambda subdir=None: (output_dir / subdir) if subdir else output_dir,
    )

    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


# ===========================================================================
# _match_prs_to_properties — gauge matching + dedup
# ===========================================================================

class TestPrsGaugeMatch:
    """Trades without a property_id should match via reference gauge."""

    def test_gauge_only_trade_matches_via_reference_gauge(
            self, tmp_path, monkeypatch):
        """Trade has property_id='' but gauge_id matches property's
        reference gauge → should attach to the property."""
        pf = _make_prop_flood()
        trade = _make_prs_trade(
            swap_id='PRS-GAUGE-ONLY',
            gauge_id='GAUGE-001',
            property_id='',
            notional=100_000,
            trade_type='InterDealerPRS',
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        prop = data['properties'][0]
        swap_ids = [t['swap_id'] for t in prop['prs_trades']]
        assert 'PRS-GAUGE-ONLY' in swap_ids
        assert prop['prs_payout'] == 100_000

    def test_direct_and_gauge_match_dedup(self, tmp_path, monkeypatch):
        """A trade with both a matching property_id AND matching gauge_id
        must appear exactly once (swap_id dedup)."""
        pf = _make_prop_flood()
        trade = _make_prs_trade(
            swap_id='PRS-DUP',
            gauge_id='GAUGE-001',
            property_id=PROP_ID,
            notional=300_000,
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        data = r.get_json()
        prop = data['properties'][0]
        dup_hits = [t for t in prop['prs_trades'] if t['swap_id'] == 'PRS-DUP']
        assert len(dup_hits) == 1
        assert prop['prs_payout'] == 300_000


# ===========================================================================
# _load_all_prs_trades — edge cases
# ===========================================================================

class TestLoadAllPrsTrades:

    def test_missing_prs_dir_skips_enrichment(self, tmp_path, monkeypatch):
        """When the prs/ subdir does not exist, derivatives are all zeros."""
        pf = _make_prop_flood()
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            include_prs_dir=False,
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        assert data['derivatives']['total_prs_payout'] == 0
        assert data['derivatives']['num_trades_triggered'] == 0
        assert data['properties'][0]['prs_trades'] == []

    def test_corrupt_prs_file_is_skipped(self, tmp_path, monkeypatch):
        """A corrupt PRS JSON file is logged and skipped, not fatal."""
        from config import config

        pts_dir = tmp_path / 'propertyts'
        pts_dir.mkdir()
        gaugets_dir = tmp_path / 'gaugets'
        gaugets_dir.mkdir()
        output_dir = tmp_path / 'output'
        output_dir.mkdir()
        prs_dir = output_dir / 'prs'
        prs_dir.mkdir()

        (pts_dir / f'{PROP_ID}.json').write_text(json.dumps(_make_prop_flood()))
        (tmp_path / 'property.json').write_text(
            json.dumps(_make_prop_details()))
        (tmp_path / 'mortgage.json').write_text(json.dumps(_make_mortgage()))

        # One valid trade, one corrupt
        good = _make_prs_trade('PRS-GOOD', 'GAUGE-001', PROP_ID, 200_000)
        (prs_dir / 'PRS-GOOD.json').write_text(json.dumps(good))
        (prs_dir / 'PRS-BROKEN.json').write_text('{not valid json')

        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
        monkeypatch.setattr(config, 'get_input_path',
                            lambda f: tmp_path / f)
        monkeypatch.setattr(
            config, 'get_reports_dir',
            lambda subdir=None: (output_dir / subdir) if subdir else output_dir,
        )

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        # Only the good trade contributes
        assert data['derivatives']['num_trades_triggered'] == 1
        assert data['derivatives']['total_prs_notional'] == 200_000

    def test_trade_with_empty_gauge_basket(self, tmp_path, monkeypatch):
        """Trade with empty GaugeBasket → gauge_id='' → direct match only."""
        trade = _make_prs_trade(
            swap_id='PRS-NO-GAUGE',
            gauge_id=None,  # empty basket
            property_id=PROP_ID,
            notional=150_000,
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        data = r.get_json()
        prop = data['properties'][0]
        # Direct property_id match succeeds despite empty gauge basket
        assert prop['prs_payout'] == 150_000
        assert prop['prs_trades'][0]['swap_id'] == 'PRS-NO-GAUGE'


# ===========================================================================
# _load_gauge_elevations — fallback and exception paths
# ===========================================================================

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
