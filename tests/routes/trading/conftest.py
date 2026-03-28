# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Shared fixtures for trading route endpoint tests.

Test data constants and factory functions live in _data.py.
This file provides pytest fixtures only.
"""

import json

import pytest

from ._data import (  # noqa: F401 — re-export for test files that import from conftest
    GAUGE_WESTMINSTER, GAUGE_CHELSEA, GAUGE_LAMBETH,
    GAUGE_VAUXHALL, GAUGE_WATERLOO, GAUGE_BLACKFRIARS, GAUGE_LONDON,
    ALL_TEST_GAUGE_IDS,
    make_trade, make_gauge_entry,
    SAMPLE_GAUGEHC, SAMPLE_GAUGE_JSON,
    CORE_TRADES, EXTENDED_TRADES, ALL_TRADES, TOTAL_TRADES,
    STORM_PORT_SEVERE, STORM_PORT_ALERT, SAMPLE_PORT_STRESS_STORMS,
    STORM_SEVERE, STORM_WARNING, SAMPLE_STRESS_STORMS,
)

# Backward compatibility: old imports used _CORE_TRADES / _EXTENDED_TRADES
_CORE_TRADES = CORE_TRADES
_EXTENDED_TRADES = EXTENDED_TRADES
_make_gauge_entry = make_gauge_entry


@pytest.fixture
def trading_env(tmp_path, monkeypatch):
    """Create isolated trading environment with 7 Thames Central gauges and 16 trades.

    Directory layout mirrors config path helpers:
        tmp_path/
            input/
                gaugehc.json, gauge.json, property.json
                gaugets/    <- per-gauge storm timeseries
            output/
                trading/    <- market_state.json, trade_marks.json
                    eod/    <- EOD snapshots
                prs/        <- PRS trade JSON files
    """
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir(parents=True)
    trading_dir = output_dir / 'trading'
    trading_dir.mkdir(parents=True)
    eod_dir = trading_dir / 'eod'
    eod_dir.mkdir()
    prs_dir = output_dir / 'prs'
    prs_dir.mkdir(parents=True)
    gaugets_dir = input_dir / 'gaugets'
    gaugets_dir.mkdir()

    with open(input_dir / 'gaugehc.json', 'w') as f:
        json.dump(SAMPLE_GAUGEHC, f)
    with open(input_dir / 'gauge.json', 'w') as f:
        json.dump(SAMPLE_GAUGE_JSON, f)
    with open(input_dir / 'property.json', 'w') as f:
        json.dump({'properties': []}, f)

    for t in ALL_TRADES:
        sid = t['PhysicalSwap']['Header']['SwapID']
        with open(prs_dir / f'{sid}.json', 'w') as f:
            json.dump(t, f)

    for gid in (GAUGE_WESTMINSTER, GAUGE_LAMBETH):
        readings = [
            {'timestamp': f'2024-06-01T{h:02d}:00:00',
             'waterLevel': round(3.5 + 2.0 * h / 72.0, 3)}
            for h in range(72)
        ]
        with open(gaugets_dir / f'{gid}.json', 'w') as f:
            json.dump({
                'gauge_id': gid,
                'flood_simulation': {'readings': readings},
                'storm_responses': [],
            }, f)

    from config import config
    monkeypatch.setattr(config, 'get_input_dir', lambda: input_dir)
    monkeypatch.setattr(config, 'get_input_path',
                        lambda filename: input_dir / filename)
    monkeypatch.setattr(config, 'get_trading_dir', lambda: trading_dir)
    monkeypatch.setattr(config, 'get_eod_dir', lambda: eod_dir)
    monkeypatch.setattr(config, 'get_reports_dir',
                        lambda subdir=None: (output_dir / subdir)
                        if subdir else output_dir)
    monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
    monkeypatch.setattr(config, 'get_gaugehd_dir',
                        lambda: input_dir / 'gaugehd')
    monkeypatch.setattr(config, 'get_output_dir', lambda: output_dir)
    stressm_dir = input_dir / 'stressm'
    stressm_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(config, 'get_stressm_dir', lambda: stressm_dir)
    classifiers_dir = input_dir / 'classifiers'
    classifiers_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(config, 'get_classifiers_dir', lambda: classifiers_dir)

    try:
        import routes.trading.stress._helpers as stress_helpers
        stress_helpers._stress_storms_cache = None
    except ImportError:
        pass

    return {
        'tmp_path': tmp_path,
        'input_dir': input_dir,
        'output_dir': output_dir,
        'trading_dir': trading_dir,
        'eod_dir': eod_dir,
        'prs_dir': prs_dir,
        'gaugets_dir': gaugets_dir,
        'stressm_dir': stressm_dir,
        'classifiers_dir': classifiers_dir,
    }


@pytest.fixture
def trading_client(trading_env):
    """Flask test client with full trading environment."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def empty_trading_env(tmp_path, monkeypatch):
    """Trading environment with no PRS trades (empty prs/ directory)."""
    input_dir = tmp_path / 'input'
    input_dir.mkdir()
    output_dir = tmp_path / 'output'
    output_dir.mkdir(parents=True)
    trading_dir = output_dir / 'trading'
    trading_dir.mkdir(parents=True)
    eod_dir = trading_dir / 'eod'
    eod_dir.mkdir()
    prs_dir = output_dir / 'prs'
    prs_dir.mkdir(parents=True)

    with open(input_dir / 'gaugehc.json', 'w') as f:
        json.dump(SAMPLE_GAUGEHC, f)
    with open(input_dir / 'gauge.json', 'w') as f:
        json.dump(SAMPLE_GAUGE_JSON, f)
    with open(input_dir / 'property.json', 'w') as f:
        json.dump({'properties': []}, f)

    from config import config
    monkeypatch.setattr(config, 'get_input_dir', lambda: input_dir)
    monkeypatch.setattr(config, 'get_input_path',
                        lambda filename: input_dir / filename)
    monkeypatch.setattr(config, 'get_trading_dir', lambda: trading_dir)
    monkeypatch.setattr(config, 'get_eod_dir', lambda: eod_dir)
    monkeypatch.setattr(config, 'get_reports_dir',
                        lambda subdir=None: (output_dir / subdir)
                        if subdir else output_dir)
    monkeypatch.setattr(config, 'get_gaugets_dir',
                        lambda: input_dir / 'gaugets')
    monkeypatch.setattr(config, 'get_gaugehd_dir',
                        lambda: input_dir / 'gaugehd')
    monkeypatch.setattr(config, 'get_output_dir', lambda: output_dir)
    stressm_dir = input_dir / 'stressm'
    stressm_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(config, 'get_stressm_dir', lambda: stressm_dir)
    classifiers_dir = input_dir / 'classifiers'
    classifiers_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(config, 'get_classifiers_dir', lambda: classifiers_dir)

    return {
        'tmp_path': tmp_path,
        'input_dir': input_dir,
        'output_dir': output_dir,
        'trading_dir': trading_dir,
        'eod_dir': eod_dir,
        'prs_dir': prs_dir,
        'classifiers_dir': classifiers_dir,
    }


@pytest.fixture
def empty_trading_client(empty_trading_env):
    """Flask test client with no trades."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def stress_env(trading_env):
    """Trading env with stress_storms/ directory written."""
    ss_dir = trading_env['input_dir'] / 'stress_storms'
    ss_dir.mkdir(exist_ok=True)

    # Write individual storm files + index
    storms = SAMPLE_STRESS_STORMS.get('storms', [])
    index_entries = []
    for storm in storms:
        storm_file = ss_dir / f"{storm['storm_id']}.json"
        with open(storm_file, 'w') as f:
            json.dump(storm, f)
        gauge_ids_alert = [
            r['gauge_id'] for r in storm.get('gauge_responses', [])
            if r.get('exceeded_alert')
        ]
        entry = {k: v for k, v in storm.items() if k != 'gauge_responses'}
        entry['gauge_ids_alert'] = gauge_ids_alert
        index_entries.append(entry)

    index = {
        'total_storms': len(storms),
        'storms': index_entries,
    }
    with open(ss_dir / '_index.json', 'w') as f:
        json.dump(index, f)

    # Clear cached data
    import routes.trading.stress._helpers as stress_helpers
    stress_helpers._stress_index_cache = None
    stress_helpers._predictor_cache = None

    return trading_env


@pytest.fixture
def stress_client(stress_env):
    """Flask client with stress data available."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()


@pytest.fixture
def port_stress_env(trading_env):
    """Trading env with stress_storms/ directory and port_stress caches cleared."""
    ss_dir = trading_env['input_dir'] / 'stress_storms'
    ss_dir.mkdir(exist_ok=True)

    storms = SAMPLE_PORT_STRESS_STORMS.get('storms', [])
    index_entries = []
    for storm in storms:
        storm_file = ss_dir / f"{storm['storm_id']}.json"
        with open(storm_file, 'w') as f:
            json.dump(storm, f)
        gauge_ids_alert = [
            r['gauge_id'] for r in storm.get('gauge_responses', [])
            if r.get('exceeded_alert')
        ]
        entry = {k: v for k, v in storm.items() if k != 'gauge_responses'}
        entry['gauge_ids_alert'] = gauge_ids_alert
        index_entries.append(entry)

    with open(ss_dir / '_index.json', 'w') as f:
        json.dump({'total_storms': len(storms), 'storms': index_entries}, f)

    # Remove any gaugets files from trading_env so the port stress code
    # uses the flat hydrograph fallback (peak_level_m from storm data).
    # This ensures threshold classification matches the storm data exactly.
    gaugets_dir = trading_env['input_dir'] / 'gaugets'
    gaugets_dir.mkdir(exist_ok=True)
    import shutil
    for gf in gaugets_dir.glob('*.json'):
        gf.unlink()

    import routes.trading.stress._helpers as stress_helpers
    stress_helpers._stress_index_cache = None
    import routes.trading.port_stress as ps_mod
    ps_mod._stressm_predictor_cache = None
    trading_env['gaugets_dir'] = gaugets_dir
    return trading_env


@pytest.fixture
def port_stress_client(port_stress_env):
    """Flask client with portfolio stress data available."""
    from server import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()
