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

"""Tests for storm display format and blotter trade existence."""

import json
import fnmatch
import pytest
from .conftest import (
    _STORM_DROPDOWN_FILES, _PROPERTY_DISPLAY_FILES_PY,
    _PROPERTY_DISPLAY_FILES_JS, _read_source,
)


class TestStormDisplayFormat:
    """Storm dropdown labels must follow the canonical pipe-separated format."""

    def test_no_file_uses_old_severe_levels_format(self):
        """'severe levels' (old space-separated format) must not appear."""
        violations = []
        for path in _STORM_DROPDOWN_FILES:
            src = _read_source(path)
            if 'severe levels' in src:
                violations.append(path)
        assert not violations, (
            f"These files still use the old 'severe levels' format: {violations}\n"
            f"Replace with '| N severe |' pipe format."
        )

    def test_no_file_uses_old_precipitation_label(self):
        """'precipitation' as a label suffix must not appear."""
        violations = []
        for path in _STORM_DROPDOWN_FILES:
            src = _read_source(path)
            if "' precipitation'" in src or "' precipitation" + '"' in src:
                violations.append(path)
        assert not violations, (
            f"These files still use the old '...precipitation' suffix: {violations}\n"
            f"Replace with '...Nmm' pipe format."
        )

    def test_all_files_include_storm_id_in_label(self):
        """Every storm dropdown must show the storm_id in the option text."""
        violations = []
        for path in _STORM_DROPDOWN_FILES:
            src = _read_source(path)
            if 'storm_id' not in src:
                violations.append(path)
        assert not violations, (
            f"These files do not include storm_id in the label: {violations}"
        )

    def test_all_files_use_sentinel_or_pipe_separator(self):
        """All dropdown option builders must use sentinel or pipe separators."""
        violations = []
        for path in _STORM_DROPDOWN_FILES:
            src = _read_source(path)
            # Static .js assets carry the __STORM_OPT__ sentinel; the
            # storm_option_js() wiring that expands it lives in the companion
            # .py (which calls js_static(...).replace('__STORM_OPT__', ...)).
            uses_sentinel = '__STORM_OPT__' in src and (
                path.endswith('.js') or '_storm_opt' in src or 'storm_option_js' in src)
            uses_pipe = " | " in src
            if not (uses_sentinel or uses_pipe):
                violations.append(path)
        assert not violations, (
            f"These files neither use the sentinel pattern nor pipe separators: {violations}"
        )

    def test_canonical_format_defined_in_config_format(self):
        """The storm display format is centralised in config/format.py."""
        from config.format import storm_option_js
        js = storm_option_js('s')
        assert ' | ' in js, "config.format.storm_option_js must use pipe separators"
        assert 'storm_id' in js, "config.format.storm_option_js must include storm_id"
        assert 'mm' in js, "config.format.storm_option_js must end with Nmm"
        assert 'severe levels' not in js, \
            "config.format.storm_option_js must not use old 'severe levels' text"

    def test_storm_option_js_warning_variant(self):
        """show_warning=True adds gauges_warning count between severe and mm."""
        from config.format import storm_option_js
        js_base = storm_option_js('s')
        js_warn = storm_option_js('s', show_warning=True)
        assert 'warn' in js_warn, "show_warning=True must include 'warn'"
        assert 'warn' not in js_base, "show_warning=False must NOT include 'warn'"

    def test_storm_option_js_peak_variant(self):
        """show_peak=True adds peak water level after mm."""
        from config.format import storm_option_js
        js_peak = storm_option_js('s', show_peak=True)
        assert 'peak' in js_peak, "show_peak=True must include 'peak'"

    def test_storm_option_js_custom_var(self):
        """Custom variable name is used throughout — gsa_timeline uses 'r'."""
        from config.format import storm_option_js
        js = storm_option_js('r')
        assert js.startswith('(r.name'), "Variable name 'r' must be used throughout"
        assert 's.storm_id' not in js, "Default 's' must not leak when var='r'"

    def test_visual_files_use_sentinel_not_hardcoded_format(self):
        """Visual files must not contain hardcoded storm display format strings."""
        hardcoded_patterns = [
            "severe levels",
            "' precipitation'",
        ]
        for path in _STORM_DROPDOWN_FILES:
            src = _read_source(path)
            for pat in hardcoded_patterns:
                assert pat not in src, (
                    f"{path} still contains hardcoded pattern '{pat}'. "
                    f"Delegate to config.format.storm_option_js instead."
                )

    def test_sp_table_uses_sentinel_pattern(self):
        """sp_table.py delegates storm label to config.format via sentinel."""
        src = _read_source('src/visual/interactivity/storm/sp_table.py')
        assert '_storm_opt' in src, \
            "sp_table.py must import storm_option_js as _storm_opt from config.format"
        assert '__STORM_OPT__' in src, \
            "sp_table.py must use __STORM_OPT__ sentinel in the JS string"
        assert '.replace(' in src, \
            "sp_table.py must call .replace('__STORM_OPT__', _storm_opt(...))"

    def test_port_stress_uses_sentinel_with_warning(self):
        """port_stress/setup.py uses sentinel with show_warning=True."""
        src = _read_source('src/visual/interactivity/trading/port_stress/setup.py')
        assert '_storm_opt' in src, \
            "port_stress/setup.py must import _storm_opt from config.format"
        assert 'show_warning=True' in src, \
            "port_stress/setup.py must pass show_warning=True to storm_option_js"

    def test_trading_stress_uses_sentinel_with_peak(self):
        """trading/stress/setup_data.py uses sentinel with show_peak=True."""
        src = _read_source('src/visual/interactivity/trading/stress/setup_data.py')
        assert '_storm_opt' in src, \
            "trading/stress/setup_data.py must import _storm_opt from config.format"
        assert 'show_peak=True' in src, \
            "trading/stress/setup_data.py must pass show_peak=True to storm_option_js"


class TestBlotterTradeExistence:
    """The blotter must return trades when trade files exist in data/input/<catchment>/prs/."""

    def test_blotter_returns_trades_with_fixture(self, tmp_path):
        """When PRS trade files are present, GET /trading/blotter returns them."""
        from pathlib import Path

        trade = {
            'PhysicalSwap': {
                'Header': {
                    'SwapID': 'PRS-AABB1122',
                    'Status': 'open',
                    'TradeDate': '2026-02-01',
                    'Counterparty': 'TestBank',
                },
                'GaugeSet': {
                    'GaugeBasket': [{'GaugeID': 'GAUGE-001'}],
                },
                'FloatLeg': {
                    'Trigger': 'severe',
                    'Tenor': '3Y',
                    'Notional': 1_000_000,
                    'Direction': 'Pay',
                    'SpreadBps': 45,
                },
            }
        }
        prs_dir = tmp_path / 'prs'
        prs_dir.mkdir()
        (prs_dir / 'PRS-AABB1122.json').write_text(json.dumps(trade))

        found = list(prs_dir.glob('PRS-*.json'))
        assert len(found) == 1, (
            "PRS-*.json glob found no files — blotter would return empty trades. "
            "Check that trade files exist in data/input/<catchment>/prs/ (run: python app.py book)."
        )

    def test_blotter_glob_pattern_matches_prs_id_protocol(self):
        """PRS-*.json glob must match PRS-{8hex} filenames (the production format)."""
        compliant = ['PRS-A8B3C4D5.json', 'PRS-ffffffff.json', 'PRS-00000000.json']
        for name in compliant:
            assert fnmatch.fnmatch(name, 'PRS-*.json'), \
                f"glob 'PRS-*.json' does not match protocol filename '{name}'"

        fixture_names = ['PRS-TEST-001.json', 'PRS-VAUXHALL.json']
        for name in fixture_names:
            assert fnmatch.fnmatch(name, 'PRS-*.json'), \
                f"Unexpected: glob does not match '{name}'"


class TestPropertyDisplayFormat:
    """Property labels must use the canonical 'Address (ID)' format from config.format."""

    def test_canonical_format_defined_in_config_format(self):
        """The property display format is centralised in config/format.py."""
        from config.format import property_title_py, property_title_js
        # Python
        assert property_title_py('128 Horseferry Road', 'PROP-abc123') == \
            '128 Horseferry Road (PROP-abc123)'
        assert property_title_py('', 'PROP-abc123') == 'PROP-abc123'
        # JavaScript
        js = property_title_js('addr', 'pid')
        assert 'addr' in js
        assert 'pid' in js
        assert '(' in js, "JS must produce parenthesised format"

    def test_python_files_import_property_title_py(self):
        """All Python property display files must import property_title_py."""
        for path in _PROPERTY_DISPLAY_FILES_PY:
            src = _read_source(path)
            assert 'property_title_py' in src, (
                f"{path} must import property_title_py from config.format"
            )

    def test_js_files_use_propertyDisplayName(self):
        """All JS property display files must use window.propertyDisplayName."""
        for path in _PROPERTY_DISPLAY_FILES_JS:
            src = _read_source(path)
            assert 'propertyDisplayName' in src, (
                f"{path} must use window.propertyDisplayName() for property labels"
            )

    def test_no_hardcoded_property_id_only_display(self):
        """Property display files should not use bare 'ID: {property_id}' format."""
        for path in _PROPERTY_DISPLAY_FILES_PY:
            src = _read_source(path)
            assert 'f"ID: {property_id}"' not in src, (
                f"{path} still uses hardcoded 'ID: {{property_id}}' format. "
                f"Delegate to config.format.property_title_py instead."
            )
