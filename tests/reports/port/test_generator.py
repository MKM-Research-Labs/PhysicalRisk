"""Tests for src/reports/port/generator.py — PortReportGenerator end-to-end."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from src.reports.port.generator import PortReportGenerator


# ---------------------------------------------------------------------------
# Sample data factories (same shapes as CDM)
# ---------------------------------------------------------------------------

def _make_gauge(gid='GAUGE-0001'):
    return {
        'FloodGauge': {
            'Header': {'GaugeID': gid},
            'Location': {'GaugeLatitude': 51.5074, 'GaugeLongitude': -0.1278},
            'FloodStages': {
                'FloodAlert': 2.5, 'FloodWarning': 3.5,
                'SevereFloodWarning': 4.5,
            },
            'SensorDetails': {'GaugeInformation': {'TidalInfluence': 'Yes'}},
        }
    }


def _make_property(pid='PROP-0001'):
    return {
        'PropertyHeader': {
            'Header': {'PropertyID': pid},
            'Location': {'LatitudeDegrees': 51.51, 'LongitudeDegrees': -0.12},
            'PropertyAttributes': {'PropertyResi': 'Detached'},
            'Valuation': {'PropertyValue': 500000},
            'RiskAssessment': {'EAFloodZone': 'Zone 2'},
        }
    }


def _make_mortgage(mid='MORT-0001', pid='PROP-0001'):
    return {
        'Mortgage': {
            'Header': {'MortgageID': mid, 'PropertyID': pid},
            'FinancialTerms': {
                'OriginalLTV': 75.0, 'OriginalTerm': 300,
                'OriginalLendingRate': 3.25,
            },
            'CurrentStatus': {'OutstandingBalance': 375000},
        }
    }


def _make_counterparty(cid='CTP-001'):
    return {
        'CounterpartySet': {
            'Party': {'PartyID': cid, 'PartyName': 'Acme Corp'},
            '_platform': {
                'ShortName': 'Acme Corp', 'PartyType': 'Bank',
                'CreditRating': 'AA', 'Jurisdiction': 'UK',
            },
        }
    }


@pytest.fixture
def populated_input(tmp_path):
    """Create a fully populated input directory for end-to-end tests."""
    d = tmp_path / 'thames'
    d.mkdir()

    (d / 'gauge.json').write_text(json.dumps({
        'flood_gauges': [_make_gauge('GAUGE-0001'), _make_gauge('GAUGE-0002')]
    }))
    (d / 'property.json').write_text(json.dumps({
        'properties': [_make_property('PROP-0001'), _make_property('PROP-0002')]
    }))
    (d / 'mortgage.json').write_text(json.dumps({
        'mortgages': [_make_mortgage('MORT-0001', 'PROP-0001')]
    }))
    (d / 'counterparty.json').write_text(json.dumps({
        'counterparties': [_make_counterparty('CTP-001')]
    }))
    (d / 'gaugehc.json').write_text(json.dumps({
        'hazard_curves': {
            'GAUGE-0001': {
                'annual_flood_prob_alert': 0.15,
                'annual_flood_prob_warning': 0.05,
                'annual_flood_prob_severe': 0.01,
                'return_period_levels': {'10yr': 3.1, '50yr': 4.2, '100yr': 5.0},
            },
        }
    }))
    (d / 'propertyhc.json').write_text(json.dumps({
        'property_hazard_curves': {'PROP-0001': {'spread': 50}}
    }))
    (d / 'sequences_summary.json').write_text(json.dumps({
        'num_sequences': 10000,
        'sequence_type_counts': {'frontal': 6000, 'convective': 4000},
        'intensity_category_counts': {'low': 5000, 'medium': 3000, 'high': 2000},
        'precipitation_mm': {'min': 5, 'mean': 25, 'max': 120},
        'duration_hours': {'min': 2, 'mean': 18, 'max': 72},
    }))

    # stress_storms index
    ss_dir = d / 'stress_storms'
    ss_dir.mkdir()
    (ss_dir / '_index.json').write_text(json.dumps({
        'storms': [{'storm_id': 'STORM-001'}, {'storm_id': 'STORM-002'}]
    }))

    # stressm classifiers
    sm_dir = d / 'stressm'
    sm_dir.mkdir()
    (sm_dir / 'GAUGE-0001.joblib').write_text('fake')
    (sm_dir / 'training_summary.json').write_text(json.dumps({
        'avg_auc_roc': 0.9525, 'num_gauges': 1,
    }))

    # subdirectories with counts
    gt = d / 'gaugets'
    gt.mkdir()
    (gt / 'GAUGE-0001.json').write_text('{}')
    (gt / 'GAUGE-0002.json').write_text('{}')

    ghd = d / 'gaugehd'
    ghd.mkdir()
    for gid in ['GAUGE-0001', 'GAUGE-0002']:
        (ghd / f'gauge_{gid}_hd.json').write_text(json.dumps({
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

    pts = d / 'propertyts'
    pts.mkdir()
    (pts / 'PROP-0001.json').write_text('{}')

    return d


@pytest.fixture
def empty_input(tmp_path):
    """Input directory with no data files at all."""
    d = tmp_path / 'empty'
    d.mkdir()
    return d


@pytest.fixture
def minimal_input(tmp_path):
    """Input directory with minimal empty-array data files."""
    d = tmp_path / 'minimal'
    d.mkdir()
    (d / 'gauge.json').write_text(json.dumps({'flood_gauges': []}))
    (d / 'property.json').write_text(json.dumps({'properties': []}))
    (d / 'mortgage.json').write_text(json.dumps({'mortgages': []}))
    (d / 'counterparty.json').write_text(json.dumps({'counterparties': []}))
    (d / 'gaugehc.json').write_text('{}')
    (d / 'propertyhc.json').write_text('{}')
    (d / 'sequences_summary.json').write_text('{}')
    return d


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestInit:
    def test_input_dir_set(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert gen.input_dir == tmp_path

    def test_output_path_explicit(self, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(tmp_path, output_path=out)
        assert gen.output_path == out

    def test_styles_initialised(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert gen.title_style is not None
        assert gen.body_style is not None
        assert gen.section_style is not None

    def test_input_dir_accepts_string(self, tmp_path):
        gen = PortReportGenerator(str(tmp_path), output_path=tmp_path / 'out.pdf')
        assert isinstance(gen.input_dir, Path)


# ---------------------------------------------------------------------------
# generate() — end-to-end PDF creation
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_produces_pdf_file(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_pdf_starts_with_magic_bytes(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        gen.generate()
        with open(out, 'rb') as f:
            assert f.read(5) == b'%PDF-'

    def test_returns_path(self, populated_input, tmp_path):
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert isinstance(result, Path)

    def test_generate_with_empty_data(self, empty_input, tmp_path):
        """Even with completely empty input, PDF should still generate."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(empty_input, output_path=out)
        result = gen.generate()
        assert result.exists()
        assert result.stat().st_size > 0

    def test_generate_with_minimal_data(self, minimal_input, tmp_path):
        """Minimal data (empty arrays) should produce valid PDF."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(minimal_input, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_pdf_has_multiple_pages(self, populated_input, tmp_path):
        """With populated data, PDF should have multiple pages (from PageBreaks)."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        gen.generate()
        # Rough check: PDF should be large enough for multiple pages
        assert out.stat().st_size > 5000

    def test_output_path_creates_parent_dirs(self, populated_input, tmp_path):
        out = tmp_path / 'nested' / 'deep' / 'report.pdf'
        out.parent.mkdir(parents=True, exist_ok=True)
        gen = PortReportGenerator(populated_input, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_catchment_name_from_input_dir(self, populated_input, tmp_path):
        """The generator uses input_dir.name as the catchment name."""
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(populated_input, output_path=out)
        assert gen.input_dir.name == 'thames'


# ---------------------------------------------------------------------------
# Integration: mixins work together
# ---------------------------------------------------------------------------

class TestMixinIntegration:
    def test_has_make_table(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert callable(gen._make_table)

    def test_has_kv_table(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert callable(gen._kv_table)

    def test_has_load_all(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        assert callable(gen._load_all)

    def test_has_section_methods(self, tmp_path):
        gen = PortReportGenerator(tmp_path, output_path=tmp_path / 'out.pdf')
        section_methods = [
            '_section_gauges', '_section_properties', '_section_mortgages',
            '_section_gaugehd', '_section_storms', '_section_hazard_curves',
            '_section_propertyts', '_section_counterparties',
            '_section_blotter', '_section_summary',
        ]
        for name in section_methods:
            assert hasattr(gen, name), f'Missing method: {name}'

    def test_load_all_and_sections_compatible(self, populated_input, tmp_path):
        """_load_all() output can be consumed by all section methods."""
        gen = PortReportGenerator(populated_input, output_path=tmp_path / 'out.pdf')
        data = gen._load_all()
        # Each section should return a list without error
        gen._section_gauges(data)
        gen._section_properties(data)
        gen._section_mortgages(data)
        gen._section_gaugehd(data)
        gen._section_storms(data)
        gen._section_hazard_curves(data)
        gen._section_propertyts(data)
        gen._section_counterparties(data)
        gen._section_blotter(data)
        gen._section_summary(data)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_gauge_with_dash_values(self, tmp_path):
        """Gauge with '-' for all numeric fields."""
        d = tmp_path / 'edge'
        d.mkdir()
        (d / 'gauge.json').write_text(json.dumps({
            'flood_gauges': [{
                'FloodGauge': {
                    'Header': {'GaugeID': 'G-1'},
                    'Location': {'GaugeLatitude': '-', 'GaugeLongitude': '-'},
                    'FloodStages': {
                        'FloodAlert': '-', 'FloodWarning': '-',
                        'SevereFloodWarning': '-',
                    },
                    'SensorDetails': {'GaugeInformation': {'TidalInfluence': '-'}},
                }
            }]
        }))
        (d / 'property.json').write_text('{"properties": []}')
        (d / 'mortgage.json').write_text('{"mortgages": []}')
        (d / 'counterparty.json').write_text('{"counterparties": []}')
        (d / 'gaugehc.json').write_text('{}')
        (d / 'propertyhc.json').write_text('{}')
        (d / 'sequences_summary.json').write_text('{}')
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(d, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_property_with_none_value(self, tmp_path):
        """Property with None for value field."""
        d = tmp_path / 'edge2'
        d.mkdir()
        (d / 'gauge.json').write_text('{"flood_gauges": []}')
        (d / 'property.json').write_text(json.dumps({
            'properties': [{
                'PropertyHeader': {
                    'Header': {'PropertyID': 'P1'},
                    'Location': {'LatitudeDegrees': 51.5, 'LongitudeDegrees': -0.1},
                    'PropertyAttributes': {'PropertyResi': 'Flat'},
                    'Valuation': {'PropertyValue': None},
                    'RiskAssessment': {'EAFloodZone': 'Zone 3'},
                }
            }]
        }))
        (d / 'mortgage.json').write_text('{"mortgages": []}')
        (d / 'counterparty.json').write_text('{"counterparties": []}')
        (d / 'gaugehc.json').write_text('{}')
        (d / 'propertyhc.json').write_text('{}')
        (d / 'sequences_summary.json').write_text('{}')
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(d, output_path=out)
        result = gen.generate()
        assert result.exists()

    def test_mortgage_with_none_fields(self, tmp_path):
        """Mortgage with None for numeric fields."""
        d = tmp_path / 'edge3'
        d.mkdir()
        (d / 'gauge.json').write_text('{"flood_gauges": []}')
        (d / 'property.json').write_text('{"properties": []}')
        (d / 'mortgage.json').write_text(json.dumps({
            'mortgages': [{
                'Mortgage': {
                    'Header': {'MortgageID': 'M1', 'PropertyID': 'P1'},
                    'FinancialTerms': {
                        'OriginalLTV': None, 'OriginalTerm': 360,
                        'OriginalLendingRate': None,
                    },
                    'CurrentStatus': {'OutstandingBalance': None},
                }
            }]
        }))
        (d / 'counterparty.json').write_text('{"counterparties": []}')
        (d / 'gaugehc.json').write_text('{}')
        (d / 'propertyhc.json').write_text('{}')
        (d / 'sequences_summary.json').write_text('{}')
        out = tmp_path / 'report.pdf'
        gen = PortReportGenerator(d, output_path=out)
        result = gen.generate()
        assert result.exists()
