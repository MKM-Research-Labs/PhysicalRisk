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

"""
Display format compliance audit.

Audits every file that renders storm, gauge, property, or counterparty
labels in the UI and reports whether each one uses the centralised
format functions from config/format.py or hardcodes the display string.

The test structure mirrors the four entity types tracked in
config/format.py:

    storm      -> storm_option_js()
    gauge      -> gauge_title_js()
    property   -> property_title_js() / property_title_py()
    counterparty -> (no centralised function yet — all hardcoded)

Each entity section defines:
    _COMPLIANT   — files that correctly use the config function
    _HARDCODED   — files with known hardcoded display strings

Tests assert that:
    1.  Every listed file exists (catches stale entries after renames).
    2.  Compliant files actually contain the expected import/sentinel.
    3.  Hardcoded files are tracked (warnings, not failures) so regressions
        are visible without breaking CI.
    4.  No NEW violations appear outside the known lists.
"""

import re
import warnings
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text()



from tests.naming_conventions._audit_display_data import (
    _STORM_COMPLIANT,
    _STORM_HARDCODED,
    _GAUGE_COMPLIANT,
    _GAUGE_HARDCODED,
    _PROPERTY_COMPLIANT_JS,
    _PROPERTY_COMPLIANT_PY,
    _PROPERTY_HARDCODED,
    _COUNTERPARTY_HARDCODED,
)


class TestStormDisplayAudit:
    """Audit storm label display across all panels."""

    @pytest.mark.parametrize('rel', _STORM_COMPLIANT)
    def test_compliant_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Compliant storm file missing: {rel}"

    @pytest.mark.parametrize('rel', _STORM_COMPLIANT)
    def test_compliant_file_uses_config(self, rel):
        src = _read(rel)
        has_sentinel = '__STORM_OPT__' in src
        has_import = 'storm_option_js' in src
        assert has_sentinel or has_import, (
            f"{rel} is listed as compliant but does not use "
            f"__STORM_OPT__ sentinel or import storm_option_js"
        )

    @pytest.mark.parametrize('rel', _STORM_HARDCODED)
    def test_hardcoded_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Hardcoded storm file missing: {rel}"

    @pytest.mark.parametrize('rel', _STORM_HARDCODED)
    def test_hardcoded_file_tracked(self, rel):
        """Warn about known hardcoded storm display — does not fail CI."""
        src = _read(rel)
        has_hardcoded = (
            "s.name" in src and "s.storm_id" in src
            or "r.name" in src and "r.storm_id" in src
        )
        if has_hardcoded:
            warnings.warn(
                f"{rel} hardcodes storm label — "
                f"should use storm_option_js from config/format.py"
            )

    def test_no_new_storm_violations(self):
        """No files outside the known lists should build storm dropdowns
        with hardcoded labels."""
        known = set(_STORM_COMPLIANT + _STORM_HARDCODED)
        pattern = re.compile(
            r"""storm_id\s*\+\s*['"]\s*\(""",
        )
        violations = []
        for search_dir in (ROOT / 'src' / 'visual', ROOT / 'src' / 'reports'):
            for py in search_dir.rglob('*.py'):
                rel = str(py.relative_to(ROOT))
                if rel in known:
                    continue
                try:
                    src = py.read_text()
                except Exception:
                    continue
                if pattern.search(src):
                    violations.append(rel)
        assert not violations, (
            f"New storm display violations found — add to "
            f"_STORM_COMPLIANT or _STORM_HARDCODED:\n"
            + '\n'.join(sorted(violations))
        )


# =========================================================================
#  Gauge display
# =========================================================================

# Files that correctly use gauge_title_js / gauge_title_py (via
# __GAUGE_TITLE__ sentinel or direct import).
_GAUGE_COMPLIANT = [
    'src/visual/interactivity/gauge/gaugesa/panel.py',
    'src/visual/interactivity/gauge/gaugehc/panel_data.py',
    'src/reports/gauge/gauge_page_01_title_overview.py',
    'src/reports/gauge/gauge_page_02_sensor_details.py',
    'src/reports/gauge/gauge_page_03_location.py',
    'src/reports/gauge/gauge_page_04_measurements.py',
    'src/reports/gauge/gauge_page_05_flood_stages.py',
    'src/reports/gauge/gauge_page_06_risk_assessment.py',
]

# Files that hardcode gauge display strings.
_GAUGE_HARDCODED = [
    'src/visual/interactivity/gauge/gaugeha.py',
    'src/visual/interactivity/context_menus.py',
    'src/visual/layer/gauge_layer/marker.py',
    'src/visual/popups/gauge_popup.py',
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
    'src/visual/interactivity/trading/market/render.py',
    'src/reports/gauge/gauge_integrator.py',
    'src/reports/port/sections.py',
    'src/reports/port/sections_portfolio.py',
]


class TestGaugeDisplayAudit:
    """Audit gauge title/label display across all panels."""

    @pytest.mark.parametrize('rel', _GAUGE_COMPLIANT)
    def test_compliant_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Compliant gauge file missing: {rel}"

    @pytest.mark.parametrize('rel', _GAUGE_COMPLIANT)
    def test_compliant_file_uses_config(self, rel):
        src = _read(rel)
        has_sentinel = '__GAUGE_TITLE__' in src
        has_import_js = 'gauge_title_js' in src
        has_import_py = 'gauge_title_py' in src
        assert has_sentinel or has_import_js or has_import_py, (
            f"{rel} is listed as compliant but does not use "
            f"__GAUGE_TITLE__ sentinel or import gauge_title_js/py"
        )

    @pytest.mark.parametrize('rel', _GAUGE_HARDCODED)
    def test_hardcoded_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Hardcoded gauge file missing: {rel}"

    @pytest.mark.parametrize('rel', _GAUGE_HARDCODED)
    def test_hardcoded_file_tracked(self, rel):
        """Warn about known hardcoded gauge display — does not fail CI."""
        src = _read(rel)
        has_gauge_ref = (
            'gauge_id' in src or 'gaugeId' in src
            or 'gauge_name' in src or 'gaugeName' in src
        )
        if has_gauge_ref:
            warnings.warn(
                f"{rel} hardcodes gauge label — "
                f"should use gauge_title_js from config/format.py"
            )

    def test_no_new_gauge_violations(self):
        """No files outside the known lists should display gauge titles
        with hardcoded name+id concatenation."""
        known = set(_GAUGE_COMPLIANT + _GAUGE_HARDCODED)
        # Match patterns like: gaugeName + ' (' + gaugeId  or
        # gauge_name + ' (' + gauge_id  (hardcoded title construction)
        pattern = re.compile(
            r"""(gaugeName|gauge_name)\s*\+\s*['"][ (]""",
        )
        violations = []
        for search_dir in (ROOT / 'src' / 'visual', ROOT / 'src' / 'reports'):
            for py in search_dir.rglob('*.py'):
                rel = str(py.relative_to(ROOT))
                if rel in known:
                    continue
                try:
                    src = py.read_text()
                except Exception:
                    continue
                if pattern.search(src):
                    violations.append(rel)
        assert not violations, (
            f"New gauge display violations found — add to "
            f"_GAUGE_COMPLIANT or _GAUGE_HARDCODED:\n"
            + '\n'.join(sorted(violations))
        )
