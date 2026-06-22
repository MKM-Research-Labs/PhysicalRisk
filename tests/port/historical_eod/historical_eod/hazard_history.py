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

"""Tests for generate_hazard_curve_history_file()."""

import pytest

import database
from db_helpers import tmp_catchment
from .conftest import generate_hazard_curve_history_file, _write_eod


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames"); the history generator reads EOD
    snapshots and persists the hazard-curve history document through ``database``."""
    with tmp_catchment(tmp_path, catchment="thames"):
        yield


def _hist():
    return database.get_hazard_curve_history(database.active_catchment())


class TestGenerateHazardCurveHistory:
    """Tests for generate_hazard_curve_history_file()."""

    def test_creates_output_file(self, tmp_path):
        _write_eod('2026-01-01')
        _write_eod('2026-01-02')
        generate_hazard_curve_history_file(database.active_catchment())
        assert _hist() is not None

    def test_output_has_metadata(self, tmp_path):
        _write_eod('2026-01-01')
        _write_eod('2026-01-02')
        generate_hazard_curve_history_file(database.active_catchment())
        data = _hist()
        assert 'metadata' in data
        assert data['metadata']['num_snapshots'] == 2

    def test_output_has_history(self, tmp_path):
        _write_eod('2026-01-01')
        generate_hazard_curve_history_file(database.active_catchment())
        data = _hist()
        assert 'history' in data
        assert 'GAUGE-001' in data['history']

    def test_no_eod_files_returns_early(self, tmp_path):
        generate_hazard_curve_history_file(database.active_catchment())
        # Nothing persisted when there are no EOD snapshots
        assert _hist() is None

    def test_multiple_gauges(self, tmp_path):
        # EOD with two gauges
        snapshot = {
            'eod_id': 'EOD-20260101',
            'date': '2026-01-01',
            'market_state_snapshot': {
                'hazard_term_structure': {
                    'GAUGE-001': {'severe': {'1': 0.03, '2': 0.04}},
                    'GAUGE-002': {'severe': {'1': 0.05, '2': 0.06}},
                }
            },
            'positions': [],
            'portfolio_summary': {},
        }
        database.save_eod_snapshot(database.active_catchment(), '2026-01-01', snapshot)
        generate_hazard_curve_history_file(database.active_catchment())
        data = _hist()
        assert 'GAUGE-001' in data['history']
        assert 'GAUGE-002' in data['history']

    def test_history_entries_have_date(self, tmp_path):
        _write_eod('2026-01-01')
        _write_eod('2026-01-02')
        generate_hazard_curve_history_file(database.active_catchment())
        entries = _hist()['history']['GAUGE-001']['severe']
        for entry in entries:
            assert 'date' in entry

    def test_metadata_lists_gauges(self, tmp_path):
        _write_eod('2026-01-01', gauge_id='GAUGE-005')
        generate_hazard_curve_history_file(database.active_catchment())
        assert 'GAUGE-005' in _hist()['metadata']['gauges']

    def test_tenors_sorted_numerically(self, tmp_path):
        _write_eod('2026-01-01')
        generate_hazard_curve_history_file(database.active_catchment())
        entries = _hist()['history']['GAUGE-001']['severe']
        assert len(entries) == 1
        entry = entries[0]
        tenor_keys = [k for k in entry if k != 'date']
        assert tenor_keys == sorted(tenor_keys, key=int)

    def test_two_eod_files_two_history_entries(self, tmp_path):
        _write_eod('2026-01-02')
        _write_eod('2026-01-03')
        generate_hazard_curve_history_file(database.active_catchment())
        entries = _hist()['history']['GAUGE-001']['severe']
        assert len(entries) == 2
