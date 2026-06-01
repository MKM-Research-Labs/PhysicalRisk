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
    return {'loans': [{'RLoan': {
        'Header': {'RLoanID': 'MORT-001', 'PropertyID': property_id},
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
        (tmp_path / 'loan.json').write_text(json.dumps(mortgage_json))
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


