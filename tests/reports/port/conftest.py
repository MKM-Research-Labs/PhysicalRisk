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
