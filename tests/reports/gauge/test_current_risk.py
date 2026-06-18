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
Tests for GaugeCurrentRiskPage.generate_elements edge-case branches
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


def _hd(obs):
    return {'daily_observations': obs, 'gauge_metadata': {}}


class TestCurrentRiskGenerateElementsEdgeCases:

    def test_no_timeseries_data(self):
        """No hd data -> 'No historical daily data' paragraph."""
        page = _make_risk_page()
        elements = page.generate_elements({}, timeseries_data=None)
        texts = [getattr(e, 'text', '') for e in elements]
        assert any('No historical daily data' in t for t in texts)

    def test_empty_daily_observations_key(self):
        """hd present but daily_observations missing -> same paragraph."""
        page = _make_risk_page()
        elements = page.generate_elements({}, timeseries_data={'historical_daily': {}})
        texts = [getattr(e, 'text', '') for e in elements]
        assert any('No historical daily data' in t for t in texts)

    def test_empty_obs_list(self):
        """daily_observations = [] -> falsy, caught by first guard."""
        page = _make_risk_page()
        elements = page.generate_elements(
            {}, timeseries_data={'historical_daily': _hd([])}
        )
        texts = [getattr(e, 'text', '') for e in elements]
        assert any('No historical daily data' in t for t in texts)

    def test_invalid_date_in_latest_obs(self):
        """Invalid date in latest observation -> current_month = None."""
        page = _make_risk_page()
        obs = [{'date': 'not-a-date', 'level_meters': 3.5}]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page.generate_elements(
                {}, timeseries_data={'historical_daily': _hd(obs)}
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0

    def test_none_level_in_obs_loop_skipped(self):
        """level is None -> skipped, does not crash."""
        page = _make_risk_page()
        obs = [
            {'date': '2024-01-15', 'level_meters': None},
            {'date': '2024-01-16', 'level_meters': 3.5},
        ]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page.generate_elements(
                {}, timeseries_data={'historical_daily': _hd(obs)}
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0

    def test_invalid_date_in_historical_loop(self):
        """ValueError/KeyError in date parse loop -> skipped."""
        page = _make_risk_page()
        obs = [
            {'date': 'bad-date', 'level_meters': 3.0},
            {'date': '2024-01-16', 'level_meters': 3.5},
        ]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page.generate_elements(
                {}, timeseries_data={'historical_daily': _hd(obs)}
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0

    def test_no_same_month_levels_uses_all_levels(self):
        """No obs in same month -> same_month_levels = all_levels."""
        page = _make_risk_page()
        obs = [
            {'date': '2023-06-10', 'level_meters': 2.0},
            {'date': '2023-06-15', 'level_meters': 2.5},
            {'date': '2024-01-20', 'level_meters': 3.0},
        ]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page.generate_elements(
                {}, timeseries_data={'historical_daily': _hd(obs)}
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 0

    def test_full_path_returns_elements(self):
        """Normal flow: valid obs -> chart + table elements returned."""
        page = _make_risk_page()
        obs = [
            {'date': f'2024-01-{d:02d}', 'level_meters': 2.5 + d * 0.1}
            for d in range(1, 31)
        ]
        ps = _stats_patch()
        for p in ps:
            p.start()
        try:
            elements = page.generate_elements(
                {}, timeseries_data={'historical_daily': _hd(obs)}
            )
        finally:
            for p in ps:
                p.stop()
        assert len(elements) > 3
