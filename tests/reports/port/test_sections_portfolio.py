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

"""Tests for portfolio-related section builders in src/reports/port/sections.py."""

from tests.reports.port.conftest import (
    _base_data,
    _has_paragraph_containing,
    _has_table,
    _make_counterparty,
    _make_gauge,
    _make_mortgage,
    _make_property,
)


# ---------------------------------------------------------------------------
# _section_propertyts
# ---------------------------------------------------------------------------

class TestSectionPropertyts:
    def test_returns_list(self, sections):
        data = _base_data(propertyts_count=10, propertyhc={})
        els = sections._section_propertyts(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(propertyts_count=0, propertyhc={})
        els = sections._section_propertyts(data)
        assert _has_paragraph_containing(els, '7. Property Flood Time Series')

    def test_phc_section_added(self, sections):
        data = _base_data(
            propertyts_count=5,
            propertyhc={'property_hazard_curves': {'P1': {}, 'P2': {}}},
        )
        els = sections._section_propertyts(data)
        assert _has_paragraph_containing(els, '8. Property Hazard Curves')
        assert _has_paragraph_containing(els, '2 property hazard curves')

    def test_no_phc_section_when_empty(self, sections):
        data = _base_data(propertyts_count=5, propertyhc={})
        els = sections._section_propertyts(data)
        assert not _has_paragraph_containing(els, '8. Property Hazard')


# ---------------------------------------------------------------------------
# _section_counterparties
# ---------------------------------------------------------------------------

class TestSectionCounterparties:
    def test_returns_list(self, sections):
        data = _base_data(counterparties=[_make_counterparty()])
        els = sections._section_counterparties(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(counterparties=[])
        els = sections._section_counterparties(data)
        assert _has_paragraph_containing(els, '9. Counterparties')

    def test_empty_message(self, sections):
        data = _base_data(counterparties=[])
        els = sections._section_counterparties(data)
        assert _has_paragraph_containing(els, 'No counterparties generated')

    def test_table_present(self, sections):
        data = _base_data(counterparties=[_make_counterparty()])
        els = sections._section_counterparties(data)
        assert _has_table(els)

    def test_alternative_cdm_format(self, sections):
        """Handles Counterparty key instead of CounterpartySet."""
        ctp = {
            'Counterparty': {
                'Header': {'CounterpartyID': 'CTP-X'},
                'Details': {'Name': 'BigBank', 'Type': 'Insurer', 'Sector': 'Finance'},
                'CreditProfile': {'Rating': 'A+'},
                'Party': {},
            }
        }
        data = _base_data(counterparties=[ctp])
        els = sections._section_counterparties(data)
        assert _has_table(els)


# ---------------------------------------------------------------------------
# _section_blotter
# ---------------------------------------------------------------------------

class TestSectionBlotter:
    def test_returns_list(self, sections):
        data = _base_data(trade_count=16, eod_count=63)
        els = sections._section_blotter(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(trade_count=0, eod_count=0)
        els = sections._section_blotter(data)
        assert _has_paragraph_containing(els, '10. Trading Book')

    def test_kv_table(self, sections):
        data = _base_data(trade_count=10, eod_count=5)
        els = sections._section_blotter(data)
        assert _has_table(els)


# ---------------------------------------------------------------------------
# _section_summary
# ---------------------------------------------------------------------------

class _FakeInputDir:
    """Fake input_dir whose rglob always returns empty."""
    def rglob(self, pattern):
        return []


class TestSectionSummary:
    def test_returns_list(self, sections):
        data = _base_data()
        # summary needs self.input_dir
        sections.input_dir = _FakeInputDir()
        els = sections._section_summary(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        sections.input_dir = _FakeInputDir()
        data = _base_data()
        els = sections._section_summary(data)
        assert _has_paragraph_containing(els, 'Summary')

    def test_kv_table_present(self, sections):
        sections.input_dir = _FakeInputDir()
        data = _base_data(
            gauges=[_make_gauge()],
            properties=[_make_property()],
            mortgages=[_make_mortgage()],
            counterparties=[_make_counterparty()],
            gaugets_count=2,
            gaugehd_count=2,
            propertyts_count=1,
            seq_summary={'num_sequences': 100},
            stress_storms={'storms': [{'storm_id': 'S1'}]},
            gaugehc={'hazard_curves': {'G1': {}}},
            propertyhc={'property_hazard_curves': {'P1': {}}},
            classifier_count=5,
            trade_count=16,
            eod_count=63,
        )
        els = sections._section_summary(data)
        assert _has_table(els)

    def test_data_size_computed(self, sections, tmp_path):
        """If input_dir is a real path, data size is appended."""
        d = tmp_path / 'catchment'
        d.mkdir()
        (d / 'test.txt').write_text('x' * 1000)
        sections.input_dir = d
        data = _base_data()
        els = sections._section_summary(data)
        assert _has_table(els)
