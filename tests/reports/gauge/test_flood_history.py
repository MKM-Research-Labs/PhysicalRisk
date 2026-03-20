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
Tests for GaugeFloodHistoryPage._build_realised_floods (page_08_flood_history.py):
  - No flood events
  - Invalid date handling
  - Multi-day event peak updates
  - Severity classification (alert/warning/severe)
  - Date formatting (single-day vs multi-day range)
"""


def _make_flood_history_page():
    from reports.gauge.gauge_page_08_flood_history import GaugeFloodHistoryPage
    return GaugeFloodHistoryPage()


def _hd_with_obs(obs, alert=4.0, warning=4.5, severe=5.0):
    return {
        'daily_observations': obs,
        'gauge_metadata': {
            'flood_stages': {
                'FloodAlert': alert,
                'FloodWarning': warning,
                'SevereFloodWarning': severe,
            }
        },
    }


class TestBuildRealisedFloods:
    """Cover uncovered lines 179-180, 190-194, 207, 209, 217 in page 08."""

    def test_no_flood_events_returns_message(self):
        """No days exceeding alert -> 'No flood events recorded'."""
        page = _make_flood_history_page()
        hd = _hd_with_obs([{'date': '2024-01-01', 'level_meters': 1.0}], alert=4.0)
        elements = page._build_realised_floods(hd)
        texts = [getattr(e, 'text', '') for e in elements]
        assert any('No flood events' in t for t in texts)

    def test_invalid_date_in_exceedance_skipped(self):
        """ValueError/TypeError in date parsing (lines 179-180) -> continue."""
        page = _make_flood_history_page()
        hd = _hd_with_obs([
            {'date': 'bad-date', 'level_meters': 5.0},
            {'date': '2024-01-10', 'level_meters': 5.0},
        ], alert=4.0)
        elements = page._build_realised_floods(hd)
        assert len(elements) > 0

    def test_multi_day_event_updates_peak(self):
        """Days within 3 days grouped; higher level updates peak."""
        page = _make_flood_history_page()
        hd = _hd_with_obs([
            {'date': '2024-01-10', 'level_meters': 4.5},
            {'date': '2024-01-11', 'level_meters': 5.5},
        ], alert=4.0, warning=4.5, severe=5.5)
        elements = page._build_realised_floods(hd)
        texts = [getattr(e, 'text', '') for e in elements]
        assert not any('No flood events' in t for t in texts)

    def test_severe_classification(self):
        """Peak >= severe_level -> 'Severe' row in table."""
        page = _make_flood_history_page()
        hd = _hd_with_obs(
            [{'date': '2024-01-10', 'level_meters': 6.0}],
            alert=4.0, warning=4.5, severe=5.0,
        )
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1

    def test_warning_classification(self):
        """warning <= peak < severe -> 'Warning'."""
        page = _make_flood_history_page()
        hd = _hd_with_obs(
            [{'date': '2024-01-10', 'level_meters': 4.6}],
            alert=4.0, warning=4.5, severe=5.0,
        )
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1

    def test_alert_classification(self):
        """alert <= peak < warning -> 'Alert'."""
        page = _make_flood_history_page()
        hd = _hd_with_obs(
            [{'date': '2024-01-10', 'level_meters': 4.2}],
            alert=4.0, warning=4.5, severe=5.0,
        )
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1

    def test_single_day_event_date_format(self):
        """Single-day flood: date_str = start.strftime(...) only."""
        page = _make_flood_history_page()
        hd = _hd_with_obs(
            [{'date': '2024-01-10', 'level_meters': 4.5}], alert=4.0,
        )
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1

    def test_multi_day_range_date_format(self):
        """Consecutive days -> single event with range format."""
        page = _make_flood_history_page()
        hd = _hd_with_obs([
            {'date': '2024-01-10', 'level_meters': 4.5},
            {'date': '2024-01-11', 'level_meters': 4.6},
        ], alert=4.0)
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1

    def test_two_separate_events(self):
        """Days > 3 days apart -> two separate flood events."""
        page = _make_flood_history_page()
        hd = _hd_with_obs([
            {'date': '2024-01-10', 'level_meters': 4.5},
            {'date': '2024-01-20', 'level_meters': 4.8},
        ], alert=4.0)
        elements = page._build_realised_floods(hd)
        assert len(elements) > 1
