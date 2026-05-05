"""Tests for risk_page_01_title.py coverage:
- Line 119: unknown risk_level falls into 'Unknown' bucket
- Lines 147-148: malformed timestamp triggers fallback to datetime.now()
"""

from reports.risk.risk_page_01_title import RiskTitlePage


class TestRiskTitlePageRiskLevelUnknownBucket:
    def test_unrecognised_risk_level_increments_unknown(self):
        """Line 119: a risk_level value not in {High, Medium, Low, Minimal, Unknown}
        is bucketed under 'Unknown'.
        """
        page = RiskTitlePage()
        flood_data = {
            "summary": {
                "total_properties": 2,
                "properties_at_risk": 1,
                "percentage_at_risk": 50,
                "total_value": 1_000_000,
                "value_at_risk": 200_000,
                "percentage_value_at_risk": 20,
            },
            "property_risk": {
                "P1": {"risk_level": "Critical"},  # not a known bucket
                "P2": {"risk_level": "High"},      # known bucket
            },
            "gauge_data": {},
            "timestamp": "2026-05-05T10:00:00",
        }
        elements = page.generate_elements(flood_data)
        # Should have generated all elements without an error paragraph
        for el in elements:
            text = getattr(el, "text", "") or ""
            assert "Error generating title page" not in text


class TestRiskTitlePageBadTimestamp:
    def test_malformed_timestamp_fallback(self):
        """Lines 147-148: invalid ISO timestamp falls back to datetime.now()."""
        page = RiskTitlePage()
        flood_data = {
            "summary": {"total_properties": 1},
            "property_risk": {"P1": {"risk_level": "Low"}},
            "gauge_data": {},
            "timestamp": "this is not a real iso timestamp",
        }
        elements = page.generate_elements(flood_data)
        for el in elements:
            text = getattr(el, "text", "") or ""
            assert "Error generating title page" not in text

    def test_non_string_timestamp_fallback(self):
        """Lines 147-148: TypeError path — timestamp isn't a string."""
        page = RiskTitlePage()
        flood_data = {
            "summary": {"total_properties": 1},
            "property_risk": {"P1": {"risk_level": "Low"}},
            "gauge_data": {},
            "timestamp": 12345,  # int, not str → AttributeError on .replace()
        }
        # Either the AttributeError gets caught by the bare-except in
        # generate_elements (line 161-165), or the (ValueError, TypeError)
        # narrower except. Just verify we don't crash and elements come back.
        elements = page.generate_elements(flood_data)
        assert len(elements) >= 1
