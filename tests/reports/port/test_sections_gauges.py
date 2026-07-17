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

"""Tests for gauge-related section builders in src/reports/port/sections.py."""

from tests.reports.port.conftest import (
    _base_data,
    _has_paragraph_containing,
    _has_table,
    _make_gauge,
    _make_property,
    _make_mortgage,
)


# ---------------------------------------------------------------------------
# _section_gauges
# ---------------------------------------------------------------------------

class TestSectionGauges:
    def test_returns_list(self, sections):
        data = _base_data(gauges=[_make_gauge()], gaugets_count=1, gaugehd_count=1)
        els = sections._section_gauges(data)
        assert isinstance(els, list)

    def test_section_heading(self, sections):
        data = _base_data(gauges=[_make_gauge()])
        els = sections._section_gauges(data)
        assert _has_paragraph_containing(els, '1. Gauge Network')

    def test_table_present(self, sections):
        data = _base_data(gauges=[_make_gauge()], gaugets_count=1, gaugehd_count=0)
        els = sections._section_gauges(data)
        assert _has_table(els)

    def test_empty_gauges_message(self, sections):
        data = _base_data()
        els = sections._section_gauges(data)
        assert _has_paragraph_containing(els, 'No gauges generated')
        assert not _has_table(els)

    def test_multiple_gauges(self, sections):
        gauges = [_make_gauge('GAUGE-0001'), _make_gauge('GAUGE-0002')]
        data = _base_data(gauges=gauges, gaugets_count=2, gaugehd_count=2)
        els = sections._section_gauges(data)
        assert _has_paragraph_containing(els, '2 gauges')

    def test_summary_line_counts(self, sections):
        data = _base_data(gauges=[_make_gauge()], gaugets_count=5, gaugehd_count=3)
        els = sections._section_gauges(data)
        assert _has_paragraph_containing(els, '5 time series')
        assert _has_paragraph_containing(els, '3 historical daily')


# ---------------------------------------------------------------------------
# _section_properties
# ---------------------------------------------------------------------------

class TestSectionProperties:
    def test_returns_list(self, sections):
        data = _base_data(properties=[_make_property()], propertyts_count=1)
        els = sections._section_properties(data)
        assert isinstance(els, list)

    def test_heading_present(self, sections):
        data = _base_data(properties=[_make_property()], propertyts_count=0)
        els = sections._section_properties(data)
        assert _has_paragraph_containing(els, '2. Properties')

    def test_table_with_properties(self, sections):
        data = _base_data(properties=[_make_property()], propertyts_count=1)
        els = sections._section_properties(data)
        assert _has_table(els)

    def test_empty_properties_message(self, sections):
        data = _base_data()
        els = sections._section_properties(data)
        assert _has_paragraph_containing(els, 'No properties generated')

    def test_property_count_in_summary(self, sections):
        props = [_make_property('PROP-001'), _make_property('PROP-002')]
        data = _base_data(properties=props, propertyts_count=2)
        els = sections._section_properties(data)
        assert _has_paragraph_containing(els, '2 properties')


# ---------------------------------------------------------------------------
# _section_mortgages
# ---------------------------------------------------------------------------

class TestSectionMortgages:
    def test_returns_list(self, sections):
        data = _base_data(mortgages=[_make_mortgage()])
        els = sections._section_mortgages(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(mortgages=[_make_mortgage()])
        els = sections._section_mortgages(data)
        assert _has_paragraph_containing(els, '3. Mortgages')

    def test_table_present(self, sections):
        data = _base_data(mortgages=[_make_mortgage()])
        els = sections._section_mortgages(data)
        assert _has_table(els)

    def test_empty_mortgages_message(self, sections):
        data = _base_data()
        els = sections._section_mortgages(data)
        assert _has_paragraph_containing(els, 'No mortgages generated')

    def test_count_in_summary(self, sections):
        morts = [_make_mortgage('M1', 'P1'), _make_mortgage('M2', 'P2')]
        data = _base_data(mortgages=morts)
        els = sections._section_mortgages(data)
        assert _has_paragraph_containing(els, '2 mortgages linked')


# ---------------------------------------------------------------------------
# _section_gaugehd
# ---------------------------------------------------------------------------

class TestSectionGaugehd:
    def test_returns_list(self, sections):
        data = _base_data(gaugehd_count=2, gaugehd_baselines=[
            {'gauge_id': 'G1', 'mean_level': 1.5, 'winter': 1.8, 'summer': 1.1},
        ])
        els = sections._section_gaugehd(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(gaugehd_count=0, gaugehd_baselines=[])
        els = sections._section_gaugehd(data)
        assert _has_paragraph_containing(els, '4. Historical Gauge Data')

    def test_table_when_baselines(self, sections):
        baselines = [
            {'gauge_id': 'G1', 'mean_level': 1.5, 'winter': 1.8, 'summer': 1.1},
            {'gauge_id': 'G2', 'mean_level': 1.6, 'winter': 1.9, 'summer': 1.2},
        ]
        data = _base_data(gaugehd_count=2, gaugehd_baselines=baselines)
        els = sections._section_gaugehd(data)
        assert _has_table(els)

    def test_no_baselines_message(self, sections):
        data = _base_data(gaugehd_count=5, gaugehd_baselines=[])
        els = sections._section_gaugehd(data)
        assert _has_paragraph_containing(els, '5 gaugehd files')

    def test_seasonal_averages(self, sections):
        baselines = [
            {'gauge_id': 'G1', 'mean_level': 1.5, 'winter': 2.0, 'summer': 1.0},
            {'gauge_id': 'G2', 'mean_level': 1.6, 'winter': 2.2, 'summer': 1.2},
        ]
        data = _base_data(gaugehd_count=2, gaugehd_baselines=baselines)
        els = sections._section_gaugehd(data)
        # Should have the avg winter/summer line
        assert _has_paragraph_containing(els, 'Avg winter baseline')

    def test_range_computed(self, sections):
        baselines = [
            {'gauge_id': 'G1', 'mean_level': 1.5, 'winter': 2.0, 'summer': 1.0},
        ]
        data = _base_data(gaugehd_count=1, gaugehd_baselines=baselines)
        els = sections._section_gaugehd(data)
        assert _has_paragraph_containing(els, 'Seasonal range')


# ---------------------------------------------------------------------------
# _section_storms
# ---------------------------------------------------------------------------

class TestSectionStorms:
    def test_returns_list(self, sections):
        data = _base_data(
            seq_summary={'num_sequences': 100},
            stress_storms={'storms': []},
            classifier_count=0,
            training_summary={},
        )
        els = sections._section_storms(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(seq_summary={}, stress_storms={})
        els = sections._section_storms(data)
        assert _has_paragraph_containing(els, '5. Storm Sequences')

    def test_kv_table_present(self, sections):
        data = _base_data(
            seq_summary={'num_sequences': 500},
            stress_storms={'storms': [{'storm_id': 'S1'}]},
            classifier_count=5,
            training_summary={'avg_auc_roc': 0.95},
        )
        els = sections._section_storms(data)
        assert _has_table(els)

    def test_with_full_summary(self, sections):
        data = _base_data(
            seq_summary={
                'num_sequences': 10000,
                'sequence_type_counts': {'frontal': 6000},
                'intensity_category_counts': {'high': 2000},
                'precipitation_mm': {'min': 5, 'mean': 25, 'max': 120},
                'duration_hours': {'min': 2, 'mean': 18, 'max': 72},
            },
            stress_storms={'storms': [{'storm_id': 'S1'}]},
            classifier_count=40,
            training_summary={'avg_auc_roc': 0.9525},
        )
        els = sections._section_storms(data)
        assert _has_table(els)


# ---------------------------------------------------------------------------
# _section_hazard_curves
# ---------------------------------------------------------------------------

class TestSectionHazardCurves:
    def test_returns_list(self, sections):
        data = _base_data(
            gaugehc={'hazard_curves': {'G1': {
                'annual_flood_prob_alert': 0.1,
                'annual_flood_prob_warning': 0.05,
                'annual_flood_prob_severe': 0.01,
                'return_period_levels': {'10yr': 3.0, '50yr': 4.0, '100yr': 5.0},
            }}},
            propertyhc={},
        )
        els = sections._section_hazard_curves(data)
        assert isinstance(els, list)

    def test_heading(self, sections):
        data = _base_data(gaugehc={}, propertyhc={})
        els = sections._section_hazard_curves(data)
        assert _has_paragraph_containing(els, '6. Hazard Curves')

    def test_no_curves_message(self, sections):
        data = _base_data(gaugehc={}, propertyhc={})
        els = sections._section_hazard_curves(data)
        assert _has_paragraph_containing(els, 'No hazard curves available')

    def test_table_with_curves(self, sections):
        data = _base_data(
            gaugehc={'hazard_curves': {
                'G1': {
                    'annual_flood_prob_alert': 0.15,
                    'annual_flood_prob_warning': 0.05,
                    'annual_flood_prob_severe': 0.01,
                    'return_period_levels': {'10yr': 3.1, '50yr': 4.2, '100yr': 5.0},
                },
            }},
            propertyhc={'property_hazard_curves': {'P1': {}}},
        )
        els = sections._section_hazard_curves(data)
        assert _has_table(els)
        assert _has_paragraph_containing(els, '1 property hazard curves')

    def test_handles_non_dict_gauge_curve(self, sections):
        """Non-dict gauge curve entry should produce dashes, not crash."""
        data = _base_data(
            gaugehc={'hazard_curves': {'G1': 'bad_value'}},
            propertyhc={},
        )
        els = sections._section_hazard_curves(data)
        assert _has_table(els)

    def test_alternative_key_format(self, sections):
        """Handles exceedance_probabilities + return_levels format."""
        data = _base_data(
            gaugehc={'hazard_curves': {'G1': {
                'exceedance_probabilities': {'alert': 0.1, 'warning': 0.05, 'severe': 0.01},
                'return_levels': {10: 3.0, 50: 4.0, 100: 5.0},
            }}},
            propertyhc={},
        )
        els = sections._section_hazard_curves(data)
        assert _has_table(els)
