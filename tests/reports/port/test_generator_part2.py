"""Tests for src/reports/port/generator.py — mixin integration and edge cases."""

import json
import pytest

from reports.port.generator import PortReportGenerator


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
        (d / 'loan.json').write_text('{"loans": []}')
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
        (d / 'loan.json').write_text('{"loans": []}')
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
        (d / 'loan.json').write_text(json.dumps({
            'loans': [{
                'RLoan': {
                    'Header': {'RLoanID': 'M1', 'PropertyID': 'P1'},
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
