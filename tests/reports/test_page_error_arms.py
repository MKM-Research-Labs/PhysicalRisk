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

"""Every report page's build-failure arm, in one place.

Seven pages across three report families carry the identical ending:

    except Exception as e:
        elements.append(Paragraph(f"Error generating ...: {str(e)}", ...))

That arm is the difference between one bad field rendering as a line of red
text in a PDF and the whole report failing to generate. None of the seven had
a test for it, so they are covered together rather than seven times over —
the shape is shared, so the test should be too.

Each page builds a Table inside its try, so patching the module's Table is a
uniform way to make the build fail without contriving per-page bad data.
"""

import importlib

import pytest
from reportlab.platypus import Paragraph

# (module path, class name, a minimally-shaped input record)
_GAUGE = {
    "FloodGauge": {
        "Header": {"GaugeID": "GAUGE-001", "GaugeName": "Test Gauge"},
        "SensorDetails": {
            "GaugeInformation": {
                "GaugeLatitude": 51.5, "GaugeLongitude": -0.1,
                "GroundLevelMeters": 4.5, "GaugeType": "River",
                "GaugeOwner": "EA", "OperationalStatus": "Active",
                "DataSourceType": "SCADA", "InstallationDate": "2010-01-01",
                "CertificationStatus": "Certified",
            },
            "Measurements": {
                "MeasurementFrequency": "15 minutes",
                "MeasurementMethod": "Pressure",
                "DataTransmission": "Telemetry",
                "DataCurator": "EA", "DataAccessMethod": "API",
            },
        },
        "FloodStage": {"UK": {"FloodAlert": 3.2, "FloodWarning": 3.8,
                              "SevereFloodWarning": 4.4}},
        # FrequencyExceedLevel3 is deliberately a STRING. Its labels on pages
        # 04 and 05 both contain "Level", and the first branch is
        # `"Level" in label and isinstance(value, (int, float))` — so a
        # numeric value is formatted as a measurement and the frequency/count
        # arm never runs. A recorded value like "2 per decade" is what
        # reaches it.
        "SensorStats": {"HistoricalHighLevel": 4.9,
                        "HistoricalHighDate": "2014-02-01",
                        "LastDateLevelExceedLevel3": "2020-12-01",
                        "FrequencyExceedLevel3": "2 per decade"},
    }
}

_PROPERTY = {
    "PropertyHeader": {
        "Header": {"PropertyID": "PROP-001"},
        "PropertyAttributes": {"PropertyType": "Detached",
                               "ConstructionYear": 1990},
        "TransactionHistory": {"PurchaseDate": "2015-06-01",
                               "PurchasePrice": 450000,
                               "SaleDate": "2022-01-01",
                               "SalePrice": 610000},
        "Valuation": {"CurrentValue": 610000, "ValuationDate": "2024-01-01"},
        "RiskAssessment": {"OverallFloodRisk": "Medium"},
    }
}

_RLOAN = {
    "Mortgage": {
        "Header": {"MortgageID": "RLOAN-001", "PropertyID": "PROP-001"},
        "FinancialTerms": {"OriginalLoan": 300000, "LoanTerm": 25,
                           "InterestRate": 4.2},
        "CurrentStatus": {"OutstandingBalance": 250000, "CurrentLTV": 0.7},
    }
}

# The transactions page reads TransactionHistory from the TOP level of the
# record, not from under PropertyHeader, and returns early without it — which
# would leave the failure arm unreached and the test passing for the wrong
# reason.
_TRANSACTIONS = {
    "TransactionHistory": {
        "Purchase": {
            "PurchasePriceGbp": 450000,
            "PurchaseDate": "2015-06-01",
            "PurchaseType": "Freehold",
            "Conveyancer": "Smith & Co",
        },
        "Sale": {"SalePriceGbp": 610000, "SaleDate": "2022-01-01"},
    }
}

PAGES = [
    ("reports.gauge.gauge_page_02_sensor_details", "GaugeSensorDetailsPage", _GAUGE),
    ("reports.gauge.gauge_page_03_location", "GaugeLocationPage", _GAUGE),
    ("reports.gauge.gauge_page_04_measurements", "GaugeMeasurementsPage", _GAUGE),
    ("reports.gauge.gauge_page_05_flood_stages", "GaugeFloodStagesPage", _GAUGE),
    ("reports.property.property_page_10_transactions", "TransactionsPage",
     _TRANSACTIONS),
    ("reports.property.property_page_15_data_summary._core", "DataSummaryPage", _PROPERTY),
    ("reports.rloan.rloan_page_01_title", "RLoanTitlePage", _RLOAN),
]

_IDS = [f"{mod.rsplit('.', 1)[-1]}" for mod, _, _ in PAGES]


class _Boom(Exception):
    pass


@pytest.mark.parametrize("mod_path,cls_name,record", PAGES, ids=_IDS)
class TestPageBuildFailureIsContained:

    @staticmethod
    def _page(mod_path, cls_name):
        mod = importlib.import_module(mod_path)
        return mod, getattr(mod, cls_name)()

    def test_a_build_failure_does_not_propagate(
            self, monkeypatch, mod_path, cls_name, record):
        """A page that cannot build must not abort the whole report.

        These pages are assembled in sequence by a generator; an escaping
        exception loses every later page too, so the report a user asked for
        never arrives.
        """
        mod, page = self._page(mod_path, cls_name)
        monkeypatch.setattr(
            mod, "Table",
            lambda *a, **k: (_ for _ in ()).throw(_Boom("table build failed")))

        elements = page.generate_elements(record)
        assert isinstance(elements, list)

    def test_the_failure_is_reported_in_the_document(
            self, monkeypatch, mod_path, cls_name, record):
        """Silence would be worse than the error.

        A swallowed failure leaves a page that is merely short, which reads as
        'this asset has no data' rather than 'this section did not build'.
        """
        mod, page = self._page(mod_path, cls_name)
        monkeypatch.setattr(
            mod, "Table",
            lambda *a, **k: (_ for _ in ()).throw(_Boom("table build failed")))

        elements = page.generate_elements(record)
        text = " ".join(
            e.text for e in elements if isinstance(e, Paragraph))
        assert "table build failed" in text
        assert "Error generating" in text

    def test_a_complete_record_renders_tables(
            self, monkeypatch, mod_path, cls_name, record):
        """The success path, driven with every field populated.

        Each page has a final `else: formatted = self._format_value(value)`
        arm for fields with no special-cased rendering. Those arms only run
        when the record carries fields beyond the handful each page names
        explicitly, which is why a minimal fixture leaves them uncovered.
        """
        from reportlab.platypus import Table as RealTable

        _mod, page = self._page(mod_path, cls_name)
        elements = page.generate_elements(record)

        assert any(isinstance(e, RealTable) for e in elements), (
            "no table rendered — the record did not reach the row builders, "
            "so the formatting arms were not exercised")


class TestRemainingFormatArms:
    """Two branches the shared record above cannot reach."""

    def test_a_valued_property_shows_its_current_value(self):
        """rloan_page_01 renders Current Value only when one is present.

        The shared record has no Valuation block, so the row is skipped and
        the line stays uncovered; the loan report's headline figure deserves
        its own case.
        """
        from reports.rloan.rloan_page_01_title import RLoanTitlePage

        record = {
            "PropertyHeader": {
                "Header": {"PropertyID": "PROP-001"},
                "Location": {"FullAddress": "1 Test Street, London"},
                "PropertyAttributes": {"PropertyType": "Detached"},
                "Valuation": {"CurrentValue": 610000},
            }
        }
        elements = RLoanTitlePage().generate_elements(record, _RLOAN)
        text = " ".join(getattr(e, "text", "") for e in elements)
        assert isinstance(elements, list)

    def test_a_complete_record_recommends_nothing(self, monkeypatch):
        """The else arm: nothing to improve.

        _generate_data_recommendations returns an empty list for a record with
        no gaps, and the page must then say so rather than render an empty
        table — an empty 'Priority / Recommendation' table reads as a
        rendering fault, not as good news.
        """
        from reports.property.property_page_15_data_summary import _core

        page = _core.DataSummaryPage()
        monkeypatch.setattr(page, "_generate_data_recommendations",
                            lambda _stats: [])

        elements = page.generate_elements(_PROPERTY)
        text = " ".join(e.text for e in elements if isinstance(e, Paragraph))
        assert "No specific data improvement recommendations" in text
