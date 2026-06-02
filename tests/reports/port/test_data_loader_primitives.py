"""Tests for src/reports/port/data_loader.py — _load and _count_dir primitives."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from reports.port.data_loader import DataLoaderMixin, _count_dir, _load


# ---------------------------------------------------------------------------
# _load()
# ---------------------------------------------------------------------------

class TestLoad:
    def test_loads_valid_json(self, tmp_path):
        p = tmp_path / 'test.json'
        p.write_text(json.dumps({'key': 'value'}))
        assert _load(p) == {'key': 'value'}

    def test_returns_empty_dict_for_missing_file(self, tmp_path):
        assert _load(tmp_path / 'nonexistent.json') == {}

    def test_returns_empty_dict_for_invalid_json(self, tmp_path):
        p = tmp_path / 'bad.json'
        p.write_text('not json at all {{{')
        assert _load(p) == {}

    def test_returns_empty_dict_for_directory(self, tmp_path):
        assert _load(tmp_path) == {}

    def test_loads_list_json(self, tmp_path):
        p = tmp_path / 'arr.json'
        p.write_text(json.dumps([1, 2, 3]))
        result = _load(p)
        assert result == [1, 2, 3]

    def test_loads_nested_json(self, tmp_path):
        data = {'a': {'b': [1, 2]}, 'c': True}
        p = tmp_path / 'nested.json'
        p.write_text(json.dumps(data))
        assert _load(p) == data


# ---------------------------------------------------------------------------
# _count_dir()
# ---------------------------------------------------------------------------

class TestCountDir:
    def test_counts_matching_files(self, tmp_path):
        for i in range(5):
            (tmp_path / f'GAUGE-{i:04d}.json').write_text('{}')
        (tmp_path / 'other.txt').write_text('')
        assert _count_dir(tmp_path, 'GAUGE-*.json') == 5

    def test_returns_zero_for_no_matches(self, tmp_path):
        (tmp_path / 'foo.txt').write_text('')
        assert _count_dir(tmp_path, '*.json') == 0

    def test_returns_zero_for_nonexistent_dir(self, tmp_path):
        assert _count_dir(tmp_path / 'nope', '*.json') == 0

    def test_returns_zero_for_none_dir(self):
        assert _count_dir(None, '*.json') == 0

    def test_empty_directory(self, tmp_path):
        assert _count_dir(tmp_path, '*') == 0


# ---------------------------------------------------------------------------
# DataLoaderMixin fixtures & helpers
# ---------------------------------------------------------------------------

def _make_gauge(gauge_id, lat=51.5, lon=-0.1, alert=2.0, warning=3.0, severe=4.0):
    return {
        'FloodGauge': {
            'Header': {'GaugeID': gauge_id},
            'Location': {'GaugeLatitude': lat, 'GaugeLongitude': lon},
            'FloodStages': {
                'FloodAlert': alert,
                'FloodWarning': warning,
                'SevereFloodWarning': severe,
            },
            'SensorDetails': {
                'GaugeInformation': {'TidalInfluence': 'Yes'},
            },
        }
    }


def _make_property(prop_id, lat=51.5, lon=-0.1, value=500000):
    return {
        'PropertyHeader': {
            'Header': {'PropertyID': prop_id},
            'Location': {'LatitudeDegrees': lat, 'LongitudeDegrees': lon},
            'PropertyAttributes': {'PropertyResi': 'Detached'},
            'Valuation': {'PropertyValue': value},
            'RiskAssessment': {'EAFloodZone': 'Zone 2'},
        }
    }


def _make_mortgage(mortgage_id, prop_id, ltv=75.0, term=300, rate=3.25, balance=375000):
    return {
        'RLoan': {
            'Header': {'RLoanID': mortgage_id, 'PropertyID': prop_id},
            'FinancialTerms': {
                'OriginalLTV': ltv,
                'OriginalTerm': term,
                'OriginalLendingRate': rate,
            },
            'CurrentStatus': {'OutstandingBalance': balance},
        }
    }


def _make_counterparty(cid, name='Acme Corp', ctype='Bank', rating='AA', jurisdiction='UK'):
    return {
        'CounterpartySet': {
            'Party': {'PartyID': cid, 'PartyName': name},
            '_platform': {
                'ShortName': name,
                'PartyType': ctype,
                'CreditRating': rating,
                'Jurisdiction': jurisdiction,
            },
        }
    }


def _write_minimal_data(d):
    """Write minimal data files so _load_all() doesn't blow up."""
    (d / 'gauge.json').write_text(json.dumps({'flood_gauges': []}))
    (d / 'property.json').write_text(json.dumps({'properties': []}))
    (d / 'loan.json').write_text(json.dumps({'loans': []}))
    (d / 'counterparty.json').write_text(json.dumps({'counterparties': []}))
    (d / 'gaugehc.json').write_text('{}')
    (d / 'propertyhc.json').write_text('{}')
    (d / 'sequences_summary.json').write_text('{}')


@pytest.fixture
def input_dir(tmp_path):
    """Create a fully populated input directory."""
    d = tmp_path / 'thames'
    d.mkdir()

    # gauge.json
    (d / 'gauge.json').write_text(json.dumps({
        'flood_gauges': [_make_gauge('GAUGE-0001'), _make_gauge('GAUGE-0002')]
    }))

    # property.json
    (d / 'property.json').write_text(json.dumps({
        'properties': [_make_property('PROP-0001')]
    }))

    # loan.json
    (d / 'loan.json').write_text(json.dumps({
        'loans': [_make_mortgage('MORT-0001', 'PROP-0001')]
    }))

    # counterparty.json
    (d / 'counterparty.json').write_text(json.dumps({
        'counterparties': [_make_counterparty('CTP-001')]
    }))

    # gaugehc.json
    (d / 'gaugehc.json').write_text(json.dumps({
        'hazard_curves': {
            'GAUGE-0001': {
                'annual_flood_prob_alert': 0.15,
                'annual_flood_prob_warning': 0.05,
                'annual_flood_prob_severe': 0.01,
                'return_period_levels': {'10yr': 3.1, '50yr': 4.2, '100yr': 5.0},
            }
        }
    }))

    # propertyhc.json
    (d / 'propertyhc.json').write_text(json.dumps({
        'property_hazard_curves': {'PROP-0001': {}}
    }))

    # sequences_summary.json
    (d / 'sequences_summary.json').write_text(json.dumps({
        'num_sequences': 10000,
        'sequence_type_counts': {'frontal': 6000, 'convective': 4000},
        'intensity_category_counts': {'low': 5000, 'medium': 3000, 'high': 2000},
        'precipitation_mm': {'min': 5, 'mean': 25, 'max': 120},
        'duration_hours': {'min': 2, 'mean': 18, 'max': 72},
    }))

    # stress_storms (index-based)
    ss_dir = d / 'stress_storms'
    ss_dir.mkdir()
    (ss_dir / '_index.json').write_text(json.dumps({
        'storms': [{'storm_id': 'STORM-001'}]
    }))

    # stressm directory with classifiers
    sm_dir = d / 'stressm'
    sm_dir.mkdir()
    (sm_dir / 'GAUGE-0001.joblib').write_text('fake')
    (sm_dir / 'GAUGE-0002.joblib').write_text('fake')
    (sm_dir / 'training_summary.json').write_text(json.dumps({
        'avg_auc_roc': 0.9525, 'num_gauges': 2,
    }))

    # gaugets directory
    gt_dir = d / 'gaugets'
    gt_dir.mkdir()
    (gt_dir / 'GAUGE-0001.json').write_text('{}')
    (gt_dir / 'GAUGE-0002.json').write_text('{}')

    # gaugehd directory
    ghd_dir = d / 'gaugehd'
    ghd_dir.mkdir()
    for gid in ['GAUGE-0001', 'GAUGE-0002']:
        (ghd_dir / f'gauge_{gid}_hd.json').write_text(json.dumps({
            'gauge_metadata': {'gauge_id': gid},
            'statistics': {
                'mean_level': 1.5,
                'monthly_means': {
                    '01': 1.8, '02': 1.7, '03': 1.5, '04': 1.3,
                    '05': 1.2, '06': 1.1, '07': 1.0, '08': 1.1,
                    '09': 1.2, '10': 1.4, '11': 1.6, '12': 1.9,
                },
            },
        }))

    # propertyts directory
    pts_dir = d / 'propertyts'
    pts_dir.mkdir()
    (pts_dir / 'PROP-0001.json').write_text('{}')

    return d


class TestTradingCountException:
    """Cover lines 85-88: exception in trading count loading."""

    def test_trade_count_zero_on_config_error(self, tmp_path, monkeypatch):
        from reports.port.data_loader import DataLoaderMixin

        class _Loader(DataLoaderMixin):
            def __init__(self):
                self.input_dir = tmp_path

        loader = _Loader()
        # Make the local `from config import config` raise inside the try block
        import builtins
        real_import = builtins.__import__
        def fail_config(name, *args, **kwargs):
            if name == "config":
                raise ImportError("forced config failure")
            return real_import(name, *args, **kwargs)
        monkeypatch.setattr(builtins, "__import__", fail_config)
        data = loader._load_all()
        assert data["trade_count"] == 0
        assert data["eod_count"] == 0


class TestGaugehdBaselineException:
    """Cover lines 116-118: malformed gaugehd file."""

    def test_malformed_gaugehd_file_skipped(self, tmp_path):
        from reports.port.data_loader import DataLoaderMixin

        class _Loader(DataLoaderMixin):
            def __init__(self):
                self.input_dir = tmp_path

        gaugehd_dir = tmp_path / "gaugehd"
        gaugehd_dir.mkdir()
        # Write a malformed file that will trigger exception
        (gaugehd_dir / "gauge_GAUGE-001_hd.json").write_text("NOT JSON")
        # Write a valid file
        (gaugehd_dir / "gauge_GAUGE-002_hd.json").write_text(
            '{"gauge_metadata": {"gauge_id": "G2"}, '
            '"statistics": {"mean_level": 1.5, "monthly_means": {"12": "1.6", "01": "1.7", "02": "1.8", "06": "1.2", "07": "1.1", "08": "1.0"}}}'
        )

        loader = _Loader()
        baselines = loader._load_gaugehd_baselines(gaugehd_dir)
        # Malformed file skipped, valid file loaded
        assert len(baselines) == 1
        assert baselines[0]["gauge_id"] == "G2"


class _LoaderHelper(DataLoaderMixin):
    def __init__(self, input_dir):
        self.input_dir = Path(input_dir)
