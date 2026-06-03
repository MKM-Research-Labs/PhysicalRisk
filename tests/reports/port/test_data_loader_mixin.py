"""Tests for src/reports/port/data_loader.py — DataLoaderMixin._load_all() and _load_gaugehd_baselines()."""

import json
import pytest
from unittest.mock import patch

from reports.port.data_loader import DataLoaderMixin

from .test_data_loader_primitives import (
    _LoaderHelper,
    _write_minimal_data,
    input_dir,  # re-export fixture
)


# ---------------------------------------------------------------------------
# DataLoaderMixin._load_all()
# ---------------------------------------------------------------------------

class TestLoadAll:
    def test_loads_gauges(self, input_dir):
        loader = _LoaderHelper(input_dir)
        with patch('reports.port.data_loader.DataLoaderMixin._load_all',
                   wraps=loader._load_all):
            data = loader._load_all()
        assert len(data['gauges']) == 2

    def test_loads_properties(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert len(data['properties']) == 1

    def test_loads_mortgages(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert len(data['mortgages']) == 1

    def test_loads_counterparties(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert len(data['counterparties']) == 1

    def test_loads_gaugehc(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert 'GAUGE-0001' in data['gaugehc']['hazard_curves']

    def test_loads_propertyhc(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert 'PROP-0001' in data['propertyhc']['property_hazard_curves']

    def test_loads_seq_summary(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['seq_summary']['num_sequences'] == 10000

    def test_loads_stress_storms_index(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert len(data['stress_storms']['storms']) == 1

    def test_loads_stress_storms_legacy_fallback(self, tmp_path):
        """Falls back to stress_storms.json when _index.json is absent."""
        d = tmp_path / 'catch'
        d.mkdir()
        _write_minimal_data(d)
        (d / 'stress_storms.json').write_text(json.dumps({
            'storms': [{'storm_id': 'S1'}, {'storm_id': 'S2'}]
        }))
        data = _LoaderHelper(d)._load_all()
        assert len(data['stress_storms']['storms']) == 2

    def test_stress_storms_empty_when_neither_exists(self, tmp_path):
        d = tmp_path / 'catch'
        d.mkdir()
        _write_minimal_data(d)
        data = _LoaderHelper(d)._load_all()
        assert data['stress_storms'] == {}

    def test_classifier_count(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['classifier_count'] == 2

    def test_training_summary(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['training_summary']['avg_auc_roc'] == pytest.approx(0.9525)

    def test_gaugets_count(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['gaugets_count'] == 2

    def test_gaugehd_count(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['gaugehd_count'] == 2

    def test_propertyts_count(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert data['propertyts_count'] == 1

    def test_trade_count_defaults_zero_on_import_error(self, input_dir):
        """config import may fail in test env — defaults to 0."""
        data = _LoaderHelper(input_dir)._load_all()
        # Either it loaded from config or defaulted to 0
        assert isinstance(data['trade_count'], int)

    def test_eod_count_defaults_zero_on_import_error(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert isinstance(data['eod_count'], int)

    def test_gaugehd_baselines_loaded(self, input_dir):
        data = _LoaderHelper(input_dir)._load_all()
        assert len(data['gaugehd_baselines']) == 2

    def test_missing_files_return_empty(self, tmp_path):
        """When input dir is empty, everything defaults safely."""
        d = tmp_path / 'empty'
        d.mkdir()
        data = _LoaderHelper(d)._load_all()
        assert data['gauges'] == []
        assert data['properties'] == []
        assert data['mortgages'] == []
        assert data['counterparties'] == []
        assert data['gaugehc'] == {}
        assert data['propertyhc'] == {}
        assert data['seq_summary'] == {}
        assert data['gaugets_count'] == 0
        assert data['gaugehd_count'] == 0
        assert data['propertyts_count'] == 0
        assert data['classifier_count'] == 0
        assert data['gaugehd_baselines'] == []


# ---------------------------------------------------------------------------
# DataLoaderMixin._load_gaugehd_baselines()
# ---------------------------------------------------------------------------

class TestLoadGaugehdBaselines:
    def test_loads_baselines(self, input_dir):
        loader = _LoaderHelper(input_dir)
        baselines = loader._load_gaugehd_baselines(input_dir / 'gaugehd')
        assert len(baselines) == 2
        bl = baselines[0]
        assert bl['gauge_id'] in ('GAUGE-0001', 'GAUGE-0002')
        assert bl['mean_level'] == pytest.approx(1.5)

    def test_computes_winter_mean(self, input_dir):
        loader = _LoaderHelper(input_dir)
        baselines = loader._load_gaugehd_baselines(input_dir / 'gaugehd')
        bl = baselines[0]
        # DJF: Dec=1.9, Jan=1.8, Feb=1.7 => mean=1.8
        assert bl['winter'] == pytest.approx(1.8)

    def test_computes_summer_mean(self, input_dir):
        loader = _LoaderHelper(input_dir)
        baselines = loader._load_gaugehd_baselines(input_dir / 'gaugehd')
        bl = baselines[0]
        # JJA: Jun=1.1, Jul=1.0, Aug=1.1 => mean=1.0667
        assert bl['summer'] == pytest.approx(1.0667, abs=0.001)

    def test_returns_empty_for_nonexistent_dir(self, tmp_path):
        loader = _LoaderHelper(tmp_path)
        assert loader._load_gaugehd_baselines(tmp_path / 'nope') == []

    def test_skips_invalid_files(self, tmp_path):
        ghd = tmp_path / 'gaugehd'
        ghd.mkdir()
        (ghd / 'gauge_BAD_hd.json').write_text('not valid json {{')
        loader = _LoaderHelper(tmp_path)
        assert loader._load_gaugehd_baselines(ghd) == []

    def test_skips_files_without_mean_level(self, tmp_path):
        ghd = tmp_path / 'gaugehd'
        ghd.mkdir()
        (ghd / 'gauge_X_hd.json').write_text(json.dumps({
            'gauge_metadata': {'gauge_id': 'X'},
            'statistics': {},
        }))
        loader = _LoaderHelper(tmp_path)
        assert loader._load_gaugehd_baselines(ghd) == []

    def test_swallows_error_during_processing(self, tmp_path):
        """Lines 116-118: a non-numeric monthly mean raises float() ValueError
        inside the loop, which is caught and the file is skipped."""
        ghd = tmp_path / 'gaugehd'
        ghd.mkdir()
        (ghd / 'gauge_Z_hd.json').write_text(json.dumps({
            'gauge_metadata': {'gauge_id': 'Z'},
            'statistics': {'mean_level': 1.0,
                           'monthly_means': {'12': 'not-a-number'}},
        }))
        loader = _LoaderHelper(tmp_path)
        assert loader._load_gaugehd_baselines(ghd) == []

    def test_handles_missing_monthly_means(self, tmp_path):
        ghd = tmp_path / 'gaugehd'
        ghd.mkdir()
        (ghd / 'gauge_X_hd.json').write_text(json.dumps({
            'gauge_metadata': {'gauge_id': 'X'},
            'statistics': {'mean_level': 2.0},
        }))
        loader = _LoaderHelper(tmp_path)
        baselines = loader._load_gaugehd_baselines(ghd)
        assert len(baselines) == 1
        assert baselines[0]['winter'] is None
        assert baselines[0]['summer'] is None
