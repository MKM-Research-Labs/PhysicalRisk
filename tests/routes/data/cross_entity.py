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

"""Tests for cross-entity consistency and interactivity JS rendering."""

import json


class TestCrossEntityConsistencyAPI:
    """Test that API responses are consistent across entity types."""

    def test_listed_properties_have_flood_data(self, full_client):
        """Properties returned by list endpoint should have flood data if propertyts exists."""
        response = full_client.get('/api/v1/properties')
        assert response.status_code == 200
        properties = json.loads(response.data)['properties']

        for prop in properties:
            pid = prop.get('property_id') or prop.get('id')
            if not pid:
                continue
            flood_response = full_client.get(f'/api/v1/properties/{pid}/floods')
            assert flood_response.status_code in [200, 404], (
                f"Property {pid} floods endpoint returned {flood_response.status_code}"
            )

    def test_listed_gauges_have_timeseries(self, full_client):
        """Gauges returned by list endpoint should have valid timeseries responses."""
        response = full_client.get('/api/v1/gauges')
        assert response.status_code == 200
        gauges = json.loads(response.data)['gauges']

        for gauge in gauges:
            gid = gauge.get('gauge_id') or gauge.get('id')
            if not gid:
                continue
            ts_response = full_client.get(f'/api/v1/gauges/{gid}/timeseries')
            assert ts_response.status_code in [200, 404], (
                f"Gauge {gid} timeseries endpoint returned {ts_response.status_code}"
            )

    def test_listed_gauges_hazard_no_500(self, full_client):
        """Gauge hazard endpoint should never return 500 for listed gauges."""
        response = full_client.get('/api/v1/gauges')
        gauges = json.loads(response.data)['gauges']

        for gauge in gauges:
            gid = gauge.get('gauge_id') or gauge.get('id')
            if not gid:
                continue
            hz_response = full_client.get(f'/api/v1/gauges/{gid}/hazard')
            assert hz_response.status_code != 500, (
                f"Gauge {gid} hazard endpoint returned 500: "
                f"{json.loads(hz_response.data).get('message', '')}"
            )


class TestInteractivityJSRendering:
    """Test that all interactivity modules render JS without f-string errors."""

    def test_property_storm_analysis_renders(self):
        """PropertyStormAnalysis JS renders without f-string errors."""
        from visual.interactivity.property.propertysa import PropertyStormAnalysis
        panel = PropertyStormAnalysis()
        js = panel.get_js()
        assert len(js) > 0
        assert '<script>' in js
        assert 'PropertyStormAnalysis' in js

    def test_gauge_storm_analysis_renders(self):
        """GaugeStormAnalysis JS renders without f-string errors."""
        from visual.interactivity.gauge.gaugesa import GaugeStormAnalysis
        panel = GaugeStormAnalysis()
        js = panel.get_js()
        assert len(js) > 0
        assert '<script>' in js

    def test_gauge_hazard_curve_renders(self):
        """GaugeHazardCurve JS renders without f-string errors."""
        from visual.interactivity.gauge.gaugehc import GaugeHazardCurve
        panel = GaugeHazardCurve()
        js = panel.get_js()
        assert len(js) > 0
        assert '<script>' in js

    def test_property_hazard_curve_renders(self):
        """PropertyHazardCurvePanel JS renders without f-string errors."""
        from visual.interactivity.property.propertyhc import PropertyHazardCurvePanel
        panel = PropertyHazardCurvePanel()
        js = panel.get_js()
        assert len(js) > 0
        assert '<script>' in js

    def test_gauge_pdf_panel_renders(self):
        """GaugePDFPanel JS renders without f-string errors."""
        from visual.interactivity.gauge.gaugepdf import GaugePDFPanel
        panel = GaugePDFPanel()
        js = panel.get_js()
        assert len(js) > 0
        assert 'GaugePDFPanel' in js

    def test_property_pdf_panel_renders(self):
        """PropertyPDFPanel JS renders without f-string errors."""
        from visual.interactivity.property.propertypdf import PropertyPDFPanel
        panel = PropertyPDFPanel()
        js = panel.get_js()
        assert len(js) > 0
        assert 'PropertyPDFPanel' in js

    def test_context_menus_renders(self):
        """ContextMenuHandler JS renders without f-string errors."""
        from visual.interactivity.context_menus import ContextMenuHandler
        handler = ContextMenuHandler()
        js = handler.get_js()
        assert len(js) > 0
        assert '<script>' in js

    def test_notifications_renders(self):
        """NotificationSystem JS renders without f-string errors."""
        from visual.interactivity.notifications import NotificationSystem
        ns = NotificationSystem()
        js = ns.get_js()
        assert len(js) > 0
        assert '<script>' in js

    def test_property_storm_js_guards_empty_events(self):
        """PropertyStormAnalysis JS must guard against empty flood_events array."""
        from visual.interactivity.property.propertysa import PropertyStormAnalysis
        panel = PropertyStormAnalysis()
        js = panel.get_js()
        assert 'flood_events.length === 0' in js, (
            "renderDistribution must guard against empty flood_events array "
            "to prevent 'Array length must be a positive integer' error"
        )
