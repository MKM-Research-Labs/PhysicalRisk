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


# =========================================================================
#  Storm display
# =========================================================================

# Files that correctly use storm_option_js (via __STORM_OPT__ sentinel
# or direct import).
_STORM_COMPLIANT = [
    'src/visual/interactivity/storm/sp_table.py',
    'src/visual/interactivity/storm/fa_render.py',
    'src/visual/interactivity/gauge/gaugehc/ghc_stress_setup.py',
    'src/visual/interactivity/gauge/gaugesa/gsa_timeline.py',
    'src/visual/interactivity/property/psa_timeline.py',
    'src/visual/interactivity/trading/port_stress/setup.py',
    'src/visual/interactivity/trading/stress/setup_data.py',
]

# Files that hardcode storm labels instead of using storm_option_js.
_STORM_HARDCODED = [
    'src/visual/interactivity/gauge/gaugehc/ghc_historical.py',
]


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
        visual_dir = ROOT / 'src' / 'visual'
        violations = []
        for py in visual_dir.rglob('*.py'):
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

# Files that correctly use gauge_title_js (via __GAUGE_TITLE__ sentinel
# or direct import).
_GAUGE_COMPLIANT = [
    'src/visual/interactivity/gauge/gaugesa/panel.py',
    'src/visual/interactivity/gauge/gaugehc/panel_data.py',
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
    'src/visual/interactivity/governance/models/mg_lineage.py',
    'src/visual/interactivity/trading/market/render.py',
    'src/reports/gauge/gauge_page_01_title_overview.py',
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
        has_import = 'gauge_title_js' in src
        assert has_sentinel or has_import, (
            f"{rel} is listed as compliant but does not use "
            f"__GAUGE_TITLE__ sentinel or import gauge_title_js"
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
        visual_dir = ROOT / 'src' / 'visual'
        violations = []
        for py in visual_dir.rglob('*.py'):
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


# =========================================================================
#  Property display
# =========================================================================

# JS files using window.propertyDisplayName (canonical JS helper).
_PROPERTY_COMPLIANT_JS = [
    'src/visual/interactivity/property/propertyhc/panel.py',
    'src/visual/interactivity/property/propertyhc/panel_data.py',
    'src/visual/interactivity/property/propertysa.py',
    'src/visual/interactivity/context_menus.py',
    'src/visual/interactivity/trading/aggregate/map_view.py',
    'src/visual/interactivity/trading/client/table.py',
]

# Python files using property_title_py from config.format.
_PROPERTY_COMPLIANT_PY = [
    'src/visual/layer/property_layer/layer.py',
    'src/visual/layer/property_layer/popup.py',
    'src/visual/popups/property_popup/builder.py',
    'src/visual/layer/mortgage_layer/popup.py',
    'src/reports/property/property_page_01_title_overview.py',
    'src/reports/property/claim/page1_cover.py',
    'src/reports/risk/risk_page_06_property_details.py',
]

# Files that hardcode property display strings.
_PROPERTY_HARDCODED = [
    'src/visual/interactivity/storm/sp_sim.py',
    'src/visual/interactivity/storm/fa_render.py',
    'src/visual/interactivity/storm/sp_table.py',
]


class TestPropertyDisplayAudit:
    """Audit property label display across all panels and reports."""

    @pytest.mark.parametrize('rel', _PROPERTY_COMPLIANT_JS)
    def test_compliant_js_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Compliant property JS file missing: {rel}"

    @pytest.mark.parametrize('rel', _PROPERTY_COMPLIANT_JS)
    def test_compliant_js_file_uses_config(self, rel):
        src = _read(rel)
        assert 'propertyDisplayName' in src, (
            f"{rel} is listed as compliant but does not use "
            f"window.propertyDisplayName()"
        )

    @pytest.mark.parametrize('rel', _PROPERTY_COMPLIANT_PY)
    def test_compliant_py_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Compliant property PY file missing: {rel}"

    @pytest.mark.parametrize('rel', _PROPERTY_COMPLIANT_PY)
    def test_compliant_py_file_uses_config(self, rel):
        src = _read(rel)
        assert 'property_title_py' in src, (
            f"{rel} is listed as compliant but does not import "
            f"property_title_py from config.format"
        )

    @pytest.mark.parametrize('rel', _PROPERTY_HARDCODED)
    def test_hardcoded_file_exists(self, rel):
        assert (ROOT / rel).exists(), f"Hardcoded property file missing: {rel}"

    @pytest.mark.parametrize('rel', _PROPERTY_HARDCODED)
    def test_hardcoded_file_tracked(self, rel):
        """Warn about known hardcoded property display — does not fail CI."""
        src = _read(rel)
        if 'property_id' in src:
            warnings.warn(
                f"{rel} hardcodes property label — "
                f"should use propertyDisplayName or property_title_py"
            )

    def test_no_new_property_violations(self):
        """No files outside the known lists should display property labels
        with bare property_id in textContent/tooltip assignments."""
        known = set(
            _PROPERTY_COMPLIANT_JS + _PROPERTY_COMPLIANT_PY
            + _PROPERTY_HARDCODED
        )
        pattern = re.compile(
            r"""(textContent|bindTooltip|title)\s*[=(]\s*.*property_id""",
            re.IGNORECASE,
        )
        visual_dir = ROOT / 'src' / 'visual'
        violations = []
        for py in visual_dir.rglob('*.py'):
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
            f"New property display violations found — add to "
            f"_PROPERTY_COMPLIANT_* or _PROPERTY_HARDCODED:\n"
            + '\n'.join(sorted(violations))
        )


# =========================================================================
#  Counterparty / trade display
# =========================================================================

# No centralised format function exists yet in config/format.py.
# All counterparty and swap ID display is currently hardcoded.
# This section tracks every file that renders these labels so that when
# a counterparty_title_js / swap_id_js function is added, migration
# progress is visible.

_COUNTERPARTY_HARDCODED = [
    'src/visual/interactivity/property/phc_prs.py',
    'src/visual/interactivity/gauge/gaugehc/ghc_prs_controls.py',
    'src/visual/interactivity/trading/blotter/table.py',
    'src/visual/interactivity/trading/blotter/actions.py',
    'src/visual/interactivity/trading/client/table.py',
    'src/visual/interactivity/trading/stress/table.py',
    'src/reports/gauge/gauge_page_12_trading.py',
    'src/reports/trading/eod_page_02_positions.py',
    'src/reports/trading/eod_page_03_pnl_detail.py',
]


class TestCounterpartyDisplayAudit:
    """Audit counterparty and swap ID display.

    config/format.py does not yet define a counterparty or swap ID
    format function.  These tests track every file that renders
    counterparty / swap labels so that when a centralised function
    is introduced, migration coverage is measurable.
    """

    def test_no_centralised_counterparty_format_yet(self):
        """Document that config/format.py has no counterparty function."""
        src = _read('config/format.py')
        has_cpty = 'counterparty' in src.lower()
        if has_cpty:
            # If someone adds it, this test should be updated to promote
            # files from _COUNTERPARTY_HARDCODED to a new _COMPLIANT list.
            pytest.fail(
                "config/format.py now contains a counterparty format "
                "function — update this audit to track compliance"
            )

    @pytest.mark.parametrize('rel', _COUNTERPARTY_HARDCODED)
    def test_hardcoded_file_exists(self, rel):
        assert (ROOT / rel).exists(), (
            f"Tracked counterparty display file missing: {rel}"
        )

    @pytest.mark.parametrize('rel', _COUNTERPARTY_HARDCODED)
    def test_hardcoded_file_tracked(self, rel):
        """Warn about hardcoded counterparty/swap display."""
        src = _read(rel)
        has_cpty = 'counterparty' in src.lower()
        has_swap = 'swap_id' in src
        if has_cpty or has_swap:
            warnings.warn(
                f"{rel} hardcodes counterparty/swap label — "
                f"no centralised format function exists yet"
            )


# =========================================================================
#  Cross-entity coverage summary
# =========================================================================

class TestAuditCoverage:
    """Verify the audit itself is complete — no display files are missed."""

    def test_all_storm_dropdown_files_covered(self):
        """Every file that imports storm_option_js should appear in the
        storm compliant list."""
        visual_dir = ROOT / 'src' / 'visual'
        covered = set(_STORM_COMPLIANT)
        uncovered = []
        for py in visual_dir.rglob('*.py'):
            rel = str(py.relative_to(ROOT))
            try:
                src = py.read_text()
            except Exception:
                continue
            if 'storm_option_js' in src and rel not in covered:
                uncovered.append(rel)
        assert not uncovered, (
            f"Files importing storm_option_js but not in audit:\n"
            + '\n'.join(sorted(uncovered))
        )

    def test_all_gauge_title_files_covered(self):
        """Every file that imports gauge_title_js should appear in the
        gauge compliant list."""
        visual_dir = ROOT / 'src' / 'visual'
        covered = set(_GAUGE_COMPLIANT)
        uncovered = []
        for py in visual_dir.rglob('*.py'):
            rel = str(py.relative_to(ROOT))
            try:
                src = py.read_text()
            except Exception:
                continue
            if 'gauge_title_js' in src and rel not in covered:
                uncovered.append(rel)
        assert not uncovered, (
            f"Files importing gauge_title_js but not in audit:\n"
            + '\n'.join(sorted(uncovered))
        )

    def test_all_property_display_name_files_covered(self):
        """Every file that uses propertyDisplayName should appear in the
        property JS compliant list."""
        visual_dir = ROOT / 'src' / 'visual'
        # startup.py defines the function — don't require it in the list
        skip = {'src/visual/interactivity/startup.py'}
        covered = set(_PROPERTY_COMPLIANT_JS)
        uncovered = []
        for py in visual_dir.rglob('*.py'):
            rel = str(py.relative_to(ROOT))
            if rel in skip:
                continue
            try:
                src = py.read_text()
            except Exception:
                continue
            if 'propertyDisplayName' in src and rel not in covered:
                uncovered.append(rel)
        assert not uncovered, (
            f"Files using propertyDisplayName but not in audit:\n"
            + '\n'.join(sorted(uncovered))
        )

    def test_all_property_title_py_files_covered(self):
        """Every file that imports property_title_py should appear in the
        property PY compliant list."""
        src_dir = ROOT / 'src'
        covered = set(_PROPERTY_COMPLIANT_PY)
        # config/format.py defines the function
        skip = {'config/format.py'}
        uncovered = []
        for py in src_dir.rglob('*.py'):
            rel = str(py.relative_to(ROOT))
            if rel in skip:
                continue
            try:
                src = py.read_text()
            except Exception:
                continue
            if 'property_title_py' in src and rel not in covered:
                uncovered.append(rel)
        assert not uncovered, (
            f"Files importing property_title_py but not in audit:\n"
            + '\n'.join(sorted(uncovered))
        )
