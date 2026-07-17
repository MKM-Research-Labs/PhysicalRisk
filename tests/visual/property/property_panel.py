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

"""Tests for property hazard curve panel (PropertyHazardCurve configure/get_statistics)."""

import pytest


class TestPropertyHazardCurveConfigure:
    """Tests for propertyhc.PropertyHazardCurve.configure() and get_statistics()."""

    def test_configure_panel_width(self):
        """Lines 301-302: configure(panel_width=...) updates panel_width."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        obj.configure(panel_width="900px")
        assert obj.panel_width == "900px"

    def test_configure_panel_height(self):
        """Lines 303-304: configure(panel_height=...) updates panel_height."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        obj.configure(panel_height="700px")
        assert obj.panel_height == "700px"

    def test_configure_both(self):
        """configure(panel_width, panel_height) updates both."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        obj.configure(panel_width="1000px", panel_height="800px")
        assert obj.panel_width == "1000px"
        assert obj.panel_height == "800px"

    def test_configure_none_does_not_change(self):
        """configure() with no args leaves values unchanged."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        original_width = obj.panel_width
        original_height = obj.panel_height
        obj.configure()
        assert obj.panel_width == original_width
        assert obj.panel_height == original_height

    def test_get_statistics(self):
        """Line 308: get_statistics() returns dict with panel_width and panel_height."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        obj.configure(panel_width="750px", panel_height="550px")
        stats = obj.get_statistics()
        assert stats["panel_width"] == "750px"
        assert stats["panel_height"] == "550px"

    def test_get_statistics_returns_dict(self):
        """get_statistics() always returns a dict."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        obj = PropertyHazardCurvePanel()
        stats = obj.get_statistics()
        assert isinstance(stats, dict)
        assert "panel_width" in stats
        assert "panel_height" in stats
