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

"""Tests simulating the server-side right-click → PDF flow."""

import json
from pathlib import Path

import pytest


class TestServerReportFlow:
    """Simulate the exact flow triggered by right-click on the map."""

    def test_property_report_via_route_function(self, tmp_path, sample_property_data, sample_mortgage_data):
        """Simulate what routes/properties.py:generate_report() does."""
        from reports.property.property_generator import generate_property_report

        # This is the exact call made by routes/properties.py line 98
        report_path = generate_property_report(
            property_data=sample_property_data,
            rloan_data=sample_mortgage_data,
            output_dir=tmp_path,
            report_type='full',
            auto_open=False  # server passes True but we skip for testing
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_gauge_report_via_route_function(self, tmp_path, sample_gauge_data):
        """Simulate what routes/gauges.py:generate_report() does."""
        from reports.gauge.gauge_generator import generate_gauge_report

        # This is the exact call made by routes/gauges.py line 109
        report_path = generate_gauge_report(
            gauge_data=sample_gauge_data,
            timeseries_data=None,
            output_dir=tmp_path,
            report_type='basic',
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.suffix == '.pdf'
        assert report_path.stat().st_size > 0

    def test_property_report_with_real_data(self, tmp_path):
        """Test with actual Thames portfolio data if available."""
        portfolio_path = Path('data/input/thames/property.json')
        mortgage_path = Path('data/input/thames/loan.json')

        if not portfolio_path.exists():
            pytest.skip("Thames property portfolio not available")

        from reports.property.property_generator import generate_property_report

        with open(portfolio_path) as f:
            props = json.load(f)
        with open(mortgage_path) as f:
            morts = json.load(f)

        report_path = generate_property_report(
            property_data=props['properties'][0],
            rloan_data=morts['loans'][0],
            output_dir=tmp_path,
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.stat().st_size > 10000

    def test_gauge_report_with_real_data(self, tmp_path):
        """Test with actual Thames gauge data if available."""
        gauge_path = Path('data/input/thames/gauge.json')

        if not gauge_path.exists():
            pytest.skip("Thames gauge portfolio not available")

        from reports.gauge.gauge_generator import generate_gauge_report

        with open(gauge_path) as f:
            gauges = json.load(f)

        report_path = generate_gauge_report(
            gauge_data=gauges['flood_gauges'][0],
            output_dir=tmp_path,
            auto_open=False
        )

        assert report_path.exists()
        assert report_path.stat().st_size > 5000
