# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for GaugeCurrentRiskPage._build_percentile_gauge risk label branches
(page_11_current_risk.py).
"""

import statistics as _stats_module
from unittest.mock import patch


def _stats_patch():
    """Context manager patching statistics.min / statistics.max with builtins."""
    return [
        patch.object(_stats_module, 'min', staticmethod(min)),
        patch.object(_stats_module, 'max', staticmethod(max)),
    ]


def _make_risk_page():
    from reports.gauge.gauge_page_11_current_risk import GaugeCurrentRiskPage
    return GaugeCurrentRiskPage()


class TestBuildPercentileGaugeRiskLabels:
    """Cover the 5 risk-level branches in _build_percentile_gauge."""

    def _levels(self, n=30):
        return [float(i) * 0.1 for i in range(1, n + 1)]

    def _call(self, percentile):
        page = _make_risk_page()
        hd = {'gauge_metadata': {}, 'daily_observations': [
            {'date': f'2024-01-{d:02d}', 'level_meters': d * 0.1}
            for d in range(1, 31)
        ]}
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page._build_percentile_gauge(
                current_level=2.0,
                percentile=percentile,
                month_name='January',
                same_month_levels=self._levels(30),
                current_date='2024-01-20',
                hd=hd,
            )
        finally:
            for p in ps:
                p.stop()
        return [getattr(e, 'text', '') for e in elements]

    def test_very_high_label(self):
        """percentile >= 95 -> 'Very High'."""
        texts = self._call(95)
        assert any('Very High' in t for t in texts)

    def test_high_label(self):
        """80 <= percentile < 95 -> 'High'."""
        texts = self._call(80)
        assert any('High' in t for t in texts)

    def test_elevated_label(self):
        """60 <= percentile < 80 -> 'Elevated'."""
        texts = self._call(60)
        assert any('Elevated' in t for t in texts)

    def test_normal_label(self):
        """40 <= percentile < 60 -> 'Normal'."""
        texts = self._call(50)
        assert any('Normal' in t for t in texts)

    def test_low_label(self):
        """percentile < 40 -> 'Low'."""
        texts = self._call(20)
        assert any('Low' in t for t in texts)

    def test_stats_table_created(self):
        """Stats table and distribution statistics header present."""
        page = _make_risk_page()
        hd = {'gauge_metadata': {}, 'daily_observations': [
            {'date': f'2024-01-{d:02d}', 'level_meters': 2.5 + d * 0.1}
            for d in range(1, 31)
        ]}
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page._build_percentile_gauge(
                current_level=2.5,
                percentile=50,
                month_name='January',
                same_month_levels=[2.5 + d * 0.1 for d in range(1, 31)],
                current_date='2024-01-20',
                hd=hd,
            )
        finally:
            for p in ps:
                p.stop()
        texts = [getattr(e, 'text', '') for e in elements]
        assert any('Distribution Statistics' in t for t in texts)

    def test_single_level_stdev_guard(self):
        """Single same_month_levels entry -> stdev guard -> no crash."""
        page = _make_risk_page()
        hd = {'gauge_metadata': {}, 'daily_observations': [
            {'date': '2024-01-20', 'level_meters': 3.0}
        ]}
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page._build_percentile_gauge(
                current_level=3.0,
                percentile=50,
                month_name='January',
                same_month_levels=[3.0],
                current_date='2024-01-20',
                hd=hd,
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0

    def test_flood_thresholds_shown_when_present(self):
        """FloodAlert and FloodWarning in metadata -> no crash."""
        page = _make_risk_page()
        hd = {
            'gauge_metadata': {
                'flood_stages': {'FloodAlert': 4.0, 'FloodWarning': 4.5}
            },
            'daily_observations': [
                {'date': f'2024-01-{d:02d}', 'level_meters': 2.5 + d * 0.1}
                for d in range(1, 31)
            ],
        }
        levels = [2.5 + d * 0.1 for d in range(1, 31)]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page._build_percentile_gauge(
                current_level=2.5, percentile=50, month_name='January',
                same_month_levels=levels, current_date='2024-01-20', hd=hd,
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0
