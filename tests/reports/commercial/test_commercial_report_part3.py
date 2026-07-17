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

"""Smoke tests for the commercial PDF report. (part 3)

Covers the round trip we built in Phase A:
  - asset/ shared section renderers produce flowables against real data
  - CommercialReportGenerator emits a valid PDF that includes the
    commercial-only sections (CommercialAttributes, AccessibilityFeatures,
    Tenancy, LoanOverview)
  - the Flask route returns 200 with a base64 PDF for a real PropertyID
    and 404 for an unknown one.
"""

import base64
import json
from pathlib import Path

import pytest

from config import config


@pytest.fixture
def halong_active():
    """Switch to halong for these tests; restore at teardown."""
    with config.use_catchment("halong"):
        yield


@pytest.fixture
def first_commercial_id(halong_active):
    with open("data/input/halong/commercial.json") as f:
        data = json.load(f)
    return data["commercial_assets"][0]["CommercialAsset"]["Header"]["PropertyID"]



@pytest.fixture
def app(halong_active):
    from flask import Flask
    from routes import register_blueprints
    a = Flask(__name__)
    register_blueprints(a)
    return a


# ---------------------------------------------------------------------------
# Error-path coverage for commercial_report.py + generator.py + page modules.
# Each test below targets a specific branch that the happy-path tests don't
# exercise — missing files, broken records, open_pdf wrapper, etc.
# ---------------------------------------------------------------------------

def test_load_commercial_record_returns_none_when_file_missing(
    halong_active, tmp_path,
):
    """``_load_commercial_record`` logs + returns None when
    commercial.json is absent from the catchment dir."""
    from reports.commercial.commercial_report import _load_commercial_record
    assert _load_commercial_record("CPROP-anything", tmp_path) is None


def test_load_loan_record_returns_none_when_file_missing(
    halong_active, tmp_path,
):
    """``_load_cloan_record`` returns None when commercial_loan.json
    is absent (silent — same convention as a missing mortgage on the
    residential side)."""
    from reports.commercial.commercial_report import _load_cloan_record
    assert _load_cloan_record("CPROP-anything", tmp_path) is None


def test_load_loan_record_returns_none_when_id_not_in_file(
    halong_active,
):
    """``_load_cloan_record`` returns None when the file exists but no
    record matches the given PropertyID."""
    from pathlib import Path
    from reports.commercial.commercial_report import _load_cloan_record
    assert _load_cloan_record("CPROP-NOTREAL", Path("data/input/halong")) is None


def test_generate_commercial_report_open_pdf_branch(
    first_commercial_id, tmp_path, monkeypatch,
):
    """When ``open_pdf=True``, the PDF-opener is invoked. We monkeypatch
    open_pdf_file so the test stays headless."""
    calls = []
    import reports.utils.open_pdf as opener
    monkeypatch.setattr(opener, "open_pdf_file", lambda p: calls.append(p))
    from reports.commercial import generate_commercial_report
    path = generate_commercial_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None
    assert calls == [path], f"open_pdf_file was not called once: {calls}"


def test_generate_commercial_report_open_pdf_failure_is_swallowed(
    first_commercial_id, tmp_path, monkeypatch,
):
    """If the PDF opener raises, the function should still return the
    PDF path — the exception is logged at WARNING and absorbed."""
    import reports.utils.open_pdf as opener
    def _boom(_):
        raise RuntimeError("simulated opener failure")
    monkeypatch.setattr(opener, "open_pdf_file", _boom)
    from reports.commercial import generate_commercial_report
    path = generate_commercial_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None  # PDF was still produced


def test_generate_loan_report_returns_none_when_no_linked_loan(
    halong_active, tmp_path, monkeypatch,
):
    """Asset exists but has no commercial-loan record → returns None."""
    from reports.commercial import commercial_report as cr
    # Patch _load_cloan_record to simulate "no loan linked".
    monkeypatch.setattr(cr, "_load_cloan_record", lambda pid, _dir: None)
    # Use a real commercial id so _load_commercial_record finds the asset.
    import json as _json
    with open("data/input/halong/commercial.json") as f:
        pid = _json.load(f)["commercial_assets"][0]["CommercialAsset"]["Header"]["PropertyID"]
    assert cr.generate_cloan_report(pid, output_dir=tmp_path) is None


def test_generate_loan_report_open_pdf_branch(
    first_commercial_id, tmp_path, monkeypatch,
):
    """open_pdf=True path through generate_cloan_report."""
    calls = []
    import reports.utils.open_pdf as opener
    monkeypatch.setattr(opener, "open_pdf_file", lambda p: calls.append(p))
    from reports.commercial import generate_cloan_report
    path = generate_cloan_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None
    assert calls == [path]


def test_generate_loan_report_open_pdf_failure_is_swallowed(
    first_commercial_id, tmp_path, monkeypatch,
):
    import reports.utils.open_pdf as opener
    def _boom(_):
        raise RuntimeError("opener failure")
    monkeypatch.setattr(opener, "open_pdf_file", _boom)
    from reports.commercial import generate_cloan_report
    path = generate_cloan_report(
        first_commercial_id, output_dir=tmp_path, open_pdf=True,
    )
    assert path is not None


def test_commercial_generator_default_output_dir(halong_active):
    """``CommercialReportGenerator()`` with no output_dir uses
    config.get_reports_dir('commercial')."""
    from reports.commercial import CommercialReportGenerator
    from config import config as _cfg
    gen = CommercialReportGenerator()  # no output_dir
    assert gen.output_dir == _cfg.get_reports_dir("commercial")


def test_commercial_generator_filename_falls_back_when_no_property_id(tmp_path):
    """``_generate_filename`` handles malformed commercial records by
    falling back to ``unknown`` rather than crashing."""
    from reports.commercial import CommercialReportGenerator
    gen = CommercialReportGenerator(output_dir=tmp_path)
    name = gen._generate_filename({})  # no CommercialAsset key
    assert "unknown" in name
    name2 = gen._generate_filename({}, kind="loan_report")
    assert name2.startswith("commercial_loan_report_unknown_")


def test_loan_overview_page_renders_placeholder_for_no_loan():
    """``CLoanOverviewPage`` emits a 'No loan record linked' placeholder
    paragraph when cloan_data is None — the only branch in the page
    not exercised by the happy-path PDF tests."""
    from reports.commercial.pages.loan_overview import CLoanOverviewPage
    from reportlab.platypus import Paragraph
    page = CLoanOverviewPage()
    flowables = page.generate_elements(commercial_data={}, cloan_data=None)
    paragraphs = [f for f in flowables if isinstance(f, Paragraph)]
    text_blob = " ".join(p.text for p in paragraphs if hasattr(p, "text"))
    assert "No loan record" in text_blob


def test_asset_base_page_generate_elements_default():
    """``AssetBasePage.generate_elements()`` (called directly, no
    subclass override) returns an empty list — the no-op default."""
    from reports.asset import AssetBasePage
    assert AssetBasePage().generate_elements() == []


def test_commercial_generator_initialize_pages_populated():
    """Smoke check on _initialize_pages — both pages and categories
    dicts are populated immediately after construction."""
    from reports.commercial import CommercialReportGenerator
    gen = CommercialReportGenerator()
    assert len(gen.pages) > 10  # 14 pages registered
    assert "commercial" in gen.categories
    assert "loan" in gen.categories
    assert "loan_overview" in gen.categories["loan"]
