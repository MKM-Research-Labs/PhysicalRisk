"""Tests for the get_statistics() method on interactive map panels.

These cover the previously-uncovered final-line `return {...}` statements in
the panel classes, which are not exercised by JS-syntax/IIFE tests.
"""


class TestMortgageDetailPanelStats:
    def test_get_statistics_default(self):
        from visual.interactivity.property.mortgagedetail import MortgageDetailPanel

        panel = MortgageDetailPanel()
        stats = panel.get_statistics()
        assert stats == {"panel_width": "600px", "panel_height": "520px"}

    def test_get_statistics_custom(self):
        from visual.interactivity.property.mortgagedetail import MortgageDetailPanel

        panel = MortgageDetailPanel(panel_width="700px", panel_height="600px")
        stats = panel.get_statistics()
        assert stats["panel_width"] == "700px"
        assert stats["panel_height"] == "600px"


class TestPropertyStormAnalysisStats:
    def test_get_statistics(self):
        from visual.interactivity.property.propertysa import PropertyStormAnalysis

        panel = PropertyStormAnalysis()
        stats = panel.get_statistics()
        assert "panel_width" in stats
        assert "panel_height" in stats


class TestGaugePDFPanelStats:
    def test_get_statistics_default(self):
        from visual.interactivity.gauge.gaugepdf import GaugePDFPanel

        panel = GaugePDFPanel()
        stats = panel.get_statistics()
        assert stats == {"panel_width": "850px", "panel_height": "90vh"}

    def test_get_statistics_custom(self):
        from visual.interactivity.gauge.gaugepdf import GaugePDFPanel

        panel = GaugePDFPanel(panel_width="900px", panel_height="80vh")
        stats = panel.get_statistics()
        assert stats == {"panel_width": "900px", "panel_height": "80vh"}


class TestPropertyPDFPanelStats:
    def test_get_statistics_default(self):
        from visual.interactivity.property.propertypdf import PropertyPDFPanel

        panel = PropertyPDFPanel()
        stats = panel.get_statistics()
        assert stats == {"panel_width": "850px", "panel_height": "90vh"}

    def test_get_statistics_custom(self):
        from visual.interactivity.property.propertypdf import PropertyPDFPanel

        panel = PropertyPDFPanel(panel_width="950px", panel_height="85vh")
        stats = panel.get_statistics()
        assert stats == {"panel_width": "950px", "panel_height": "85vh"}


class TestStormPortfolioPanelStats:
    def test_get_statistics(self):
        from visual.interactivity.storm.stormportfolio.panel import StormPortfolioPanel

        panel = StormPortfolioPanel()
        stats = panel.get_statistics()
        assert "panel_width" in stats
        assert "panel_height" in stats
        assert stats["panel_width"] == "960px"
        assert stats["panel_height"] == "640px"


class TestModelGovernancePanelStats:
    def test_get_statistics(self):
        from visual.interactivity.governance.modelgovernance import ModelGovernancePanel

        panel = ModelGovernancePanel()
        stats = panel.get_statistics()
        assert "panel_width" in stats
        assert "panel_height" in stats
