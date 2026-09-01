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

"""Display format enforcement -- centralised config/format.py usage."""

import warnings
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


# Known files that SHOULD use gauge_title_js from config/format.py
_GAUGE_TITLE_FILES = [
    'src/visual/interactivity/gauge/gaugeha.py',
    'src/visual/interactivity/trading/stress/setup_data.py',
    'src/visual/interactivity/trading/blotter/filters.py',
    'src/visual/interactivity/trading/blotter/actions.py',
    'src/visual/interactivity/trading/port_stress/pfloods.py',
    'src/visual/interactivity/trading/port_stress/portfolio_pnl.py',
    'src/visual/interactivity/trading/fs01/grid.py',
    'src/visual/interactivity/trading/eod/render.py',
    'src/visual/interactivity/trading/td_main_map.py',
    'src/visual/interactivity/trading/aggregate/map_view.py',
    'src/visual/interactivity/property/phc_hazard.py',
    'src/visual/interactivity/property/propertyhc/panel_basis_strip.py',
    'src/visual/layer/gauge_layer/marker.py',
]

# Known storm label violations (not using __STORM_OPT__ sentinel)
_STORM_LABEL_VIOLATIONS = [
    'src/visual/interactivity/gauge/gaugehc/ghc_historical.py',
    'src/visual/interactivity/gauge/gaugesa/gsa_timeline.py',
]

# Known property display files
_PROPERTY_DISPLAY_FILES = [
    'src/visual/interactivity/context_menus.py',
    'src/visual/interactivity/storm/sp_table.py',
    'src/visual/layer/property_layer/layer.py',
    'src/visual/layer/property_layer/popup.py',
    'src/visual/popups/property_popup/builder.py',
]


def _read_src(rel_path: str) -> str:
    """Read a source file relative to the project root."""
    return Path(ROOT / rel_path).read_text()


# =========================================================================
# Gauge title format usage
# =========================================================================

class TestGaugeTitleFormatUsage:
    """Verify gauge title display uses the centralised config/format.py."""

    def test_config_format_defines_gauge_title(self):
        """config/format.py must export gauge_title_js with '(' and gaugeId."""
        from config.format import gauge_title_js
        result = gauge_title_js()
        assert '(' in result, (
            f"gauge_title_js() should contain '(' for name(id) format, "
            f"got: {result}"
        )
        assert 'gaugeId' in result, (
            f"gauge_title_js() should reference gaugeId, got: {result}"
        )

    def test_panel_data_uses_config_format(self):
        """gaugehc/panel_data.py must import gauge_title_js."""
        src = _read_src('src/visual/interactivity/gauge/gaugehc/panel_data.py')
        assert 'gauge_title_js' in src, (
            "panel_data.py does not import gauge_title_js from config.format"
        )

    def test_gaugesa_uses_config_format(self):
        """gaugesa/panel.py must import gauge_title_js."""
        src = _read_src('src/visual/interactivity/gauge/gaugesa/panel.py')
        assert 'gauge_title_js' in src, (
            "gaugesa/panel.py does not import gauge_title_js from config.format"
        )

    def test_known_gauge_violations_tracked(self):
        """Document known files that use gauge_name/gaugeName instead of
        gauge_title_js -- these are tracked violations to fix later."""
        for rel in _GAUGE_TITLE_FILES:
            path = ROOT / rel
            assert path.exists(), f"Known gauge title file missing: {rel}"
            src = path.read_text()
            if 'gauge_name' in src or 'gaugeName' in src:
                warnings.warn(
                    f"{rel} uses gauge_name/gaugeName instead of "
                    f"gauge_title_js -- tracked violation"
                )


# =========================================================================
# Storm format usage
# =========================================================================

class TestStormFormatUsage:
    """Verify storm dropdown labels use the centralised config/format.py."""

    def test_config_format_defines_storm_option(self):
        """config/format.py must export storm_option_js containing
        'storm_id' and '|'."""
        from config.format import storm_option_js
        result = storm_option_js()
        assert 'storm_id' in result, (
            f"storm_option_js() should reference storm_id, got: {result}"
        )
        assert '|' in result, (
            f"storm_option_js() should contain '|' separator, got: {result}"
        )

    def test_storm_dropdown_files_use_sentinel(self):
        """Files that build storm dropdowns must use __STORM_OPT__ or
        import storm_option_js."""
        # These are files known to use the sentinel or direct import
        storm_files = [
            'src/visual/interactivity/storm/sp_table.py',
            'src/visual/interactivity/storm/fa_render.py',
            'src/visual/interactivity/gauge/gaugehc/ghc_stress_setup.py',
            'src/visual/interactivity/trading/stress/setup_data.py',
            'src/visual/interactivity/trading/port_stress/setup.py',
            'src/visual/interactivity/gauge/gaugesa/gsa_timeline.py',
        ]
        for rel in storm_files:
            path = ROOT / rel
            if not path.exists():
                continue
            src = path.read_text()
            has_sentinel = '__STORM_OPT__' in src
            has_import = 'storm_option_js' in src
            assert has_sentinel or has_import, (
                f"{rel} does not use __STORM_OPT__ sentinel or "
                f"import storm_option_js"
            )

    def test_known_storm_violations_tracked(self):
        """Document known files with hardcoded storm labels instead of
        using the centralised format."""
        for rel in _STORM_LABEL_VIOLATIONS:
            path = ROOT / rel
            assert path.exists(), f"Known violation file missing: {rel}"
            src = path.read_text()
            has_hardcoded = (
                "s.name + ' (' + s.storm_id" in src
                or "r.name + ' (' + r.storm_id" in src
                or ".name ? " in src
            )
            if has_hardcoded:
                warnings.warn(
                    f"{rel} contains hardcoded storm label format -- "
                    f"should use storm_option_js from config/format.py"
                )


# =========================================================================
# Property format usage
# =========================================================================

class TestPropertyFormatUsage:
    """Verify property display labels use the centralised config/format.py."""

    def test_config_format_defines_property_title(self):
        """config/format.py must export property_title_js returning a string."""
        from config.format import property_title_js
        result = property_title_js()
        assert isinstance(result, str), (
            f"property_title_js() should return a string, got: {type(result)}"
        )

    def test_known_property_display_files_tracked(self):
        """Document known files that reference property_id in display context
        -- these should eventually use property_title_js."""
        for rel in _PROPERTY_DISPLAY_FILES:
            path = ROOT / rel
            assert path.exists(), f"Known property display file missing: {rel}"
            src = path.read_text()
            if 'property_id' in src.lower():
                warnings.warn(
                    f"{rel} uses property_id directly -- "
                    f"should use property_title_js from config/format.py"
                )

    def test_no_new_property_display_violations(self):
        """Scan all src/visual/**/*.py for property_id in textContent/label/title
        assignments -- count should not exceed known list."""
        import re
        pattern = re.compile(
            r'(textContent|label|title)\s*[=+].*property_id',
            re.IGNORECASE,
        )
        visual_dir = ROOT / 'src' / 'visual'
        violations = []
        for py_file in visual_dir.rglob('*.py'):
            try:
                src = py_file.read_text()
            except Exception:
                continue
            for match in pattern.finditer(src):
                rel = str(py_file.relative_to(ROOT))
                violations.append(rel)
        known_count = len(_PROPERTY_DISPLAY_FILES)
        unique_files = set(violations)
        assert len(unique_files) <= known_count, (
            f"Found {len(unique_files)} files with property_id display "
            f"violations, expected <= {known_count}. "
            f"New violations: {sorted(unique_files - set(_PROPERTY_DISPLAY_FILES))}"
        )
