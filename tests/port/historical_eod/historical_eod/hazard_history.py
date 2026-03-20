# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Tests for generate_hazard_curve_history_file()."""

import json
import pytest
from .conftest import generate_hazard_curve_history_file, _write_eod


class TestGenerateHazardCurveHistory:
    """Tests for generate_hazard_curve_history_file()."""

    def test_creates_output_file(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        _write_eod(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        assert output.exists()

    def test_output_has_metadata(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        _write_eod(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'metadata' in data
        assert data['metadata']['num_snapshots'] == 2

    def test_output_has_history(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'history' in data
        assert 'GAUGE-001' in data['history']

    def test_no_eod_files_returns_early(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        # No files written when dir is empty
        assert not output.exists()

    def test_multiple_gauges(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()

        # EOD with two gauges
        snapshot = {
            'eod_id': 'EOD-2026-01-01',
            'date': '2026-01-01',
            'market_state_snapshot': {
                'hazard_term_structure': {
                    'GAUGE-001': {
                        'severe': {'1': 0.03, '2': 0.04},
                    },
                    'GAUGE-002': {
                        'severe': {'1': 0.05, '2': 0.06},
                    },
                }
            },
            'positions': [],
            'portfolio_summary': {},
        }
        (eod_dir / 'EOD-2026-01-01.json').write_text(json.dumps(snapshot))
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'GAUGE-001' in data['history']
        assert 'GAUGE-002' in data['history']

    def test_history_entries_have_date(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        _write_eod(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        entries = data['history']['GAUGE-001']['severe']
        for entry in entries:
            assert 'date' in entry

    def test_metadata_lists_gauges(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01', gauge_id='GAUGE-005')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        assert 'GAUGE-005' in data['metadata']['gauges']

    def test_tenors_sorted_numerically(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-01', '2026-01-01')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        entries = data['history']['GAUGE-001']['severe']
        assert len(entries) == 1
        entry = entries[0]
        tenor_keys = [k for k in entry if k != 'date']
        assert tenor_keys == sorted(tenor_keys, key=int)

    def test_two_eod_files_two_history_entries(self, tmp_path):
        eod_dir = tmp_path / 'eod'
        eod_dir.mkdir()
        _write_eod(eod_dir, 'EOD-2026-01-02', '2026-01-02')
        _write_eod(eod_dir, 'EOD-2026-01-03', '2026-01-03')
        output = tmp_path / 'hazard_curve_history.json'

        generate_hazard_curve_history_file(eod_dir, output)

        data = json.loads(output.read_text())
        entries = data['history']['GAUGE-001']['severe']
        assert len(entries) == 2
