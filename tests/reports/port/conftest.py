"""Shared fixtures and helpers for tests/reports/port/test_sections_*.py."""

import pytest
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table

from src.reports.port.sections import SectionsMixin
from src.reports.port.styles import StylesMixin


# ---------------------------------------------------------------------------
# Concrete helper that mixes StylesMixin + SectionsMixin
# ---------------------------------------------------------------------------

class _SectionsHelper(StylesMixin, SectionsMixin):
    def __init__(self):
        self._styles = getSampleStyleSheet()
        self._setup_styles()


@pytest.fixture
def sections():
    return _SectionsHelper()


# ---------------------------------------------------------------------------
# Sample data factories
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


def _base_data(**overrides):
    """Return a minimal data dict that every section can safely consume."""
    d = {
        'gauges': [],
        'gauges_raw': {'flood_gauges': []},
        'properties': [],
        'properties_raw': {'properties': []},
        'mortgages': [],
        'mortgages_raw': {'mortgages': []},
        'counterparties': [],
        'counterparties_raw': {'counterparties': []},
        'gaugehc': {},
        'propertyhc': {},
        'seq_summary': {},
        'stress_storms': {},
        'classifier_count': 0,
        'training_summary': {},
        'gaugets_count': 0,
        'gaugehd_count': 0,
        'propertyts_count': 0,
        'trade_count': 0,
        'eod_count': 0,
        'gaugehd_baselines': [],
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Helpers for checking section output
# ---------------------------------------------------------------------------

def _has_paragraph_containing(elements, text):
    """Return True if any Paragraph element contains the given text."""
    for el in elements:
        if isinstance(el, Paragraph) and text in el.text:
            return True
    return False


def _has_table(elements):
    return any(isinstance(el, Table) for el in elements)


# ---------------------------------------------------------------------------
# Fixtures for test_generator split files
# ---------------------------------------------------------------------------

@pytest.fixture
def populated_input(tmp_path):
    """Create a fully populated input directory for end-to-end tests."""
    import json

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
    import json

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
