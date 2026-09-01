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

"""Contract tests A-C: startup ownership, cache consumers, no bare reads."""

import re

import pytest

from tests.visual.conftest import iife_src_file, iife_has_node, iife_node_check, STARTUP_CACHE_VARS


# ---------------------------------------------------------------------------
# CONTRACT A — startup.py must own all shared vars via window.*
# ---------------------------------------------------------------------------

class TestContractA_StartupOwnership:
    """startup.py must declare every shared cross-IIFE variable on window.

    If a variable is declared with ``var`` inside startup.py's IIFE, it is
    local to that function and invisible to ALL other IIFEs.  Every shared
    variable must be ``window.X = ...`` so the global object carries it.
    """

    def test_no_var_declaration_for_td_preload_done(self):
        """The preload-done flag must NOT be a var (regression: 2026-03-12 incident)."""
        src = iife_src_file('src/visual/interactivity/startup.py')
        assert 'var _tdPreloadDone' not in src, (
            'REGRESSION: var _tdPreloadDone traps it in the startup IIFE local scope. '
            'Use window._tdPreloadDone instead.'
        )

    def test_window_td_preload_done_initialised(self):
        src = iife_src_file('src/visual/interactivity/startup.py')
        assert 'window._tdPreloadDone = false' in src

    def test_window_td_preload_done_set_after_settle(self):
        src = iife_src_file('src/visual/interactivity/startup.py')
        assert 'window._tdPreloadDone = true' in src

    @pytest.mark.parametrize('var', [v for v in STARTUP_CACHE_VARS if v != '_tdPreloadDone'])
    def test_cache_var_initialised_on_window(self, var):
        """Each startup cache variable must be initialised as window.X = null."""
        src = iife_src_file('src/visual/interactivity/startup.py')
        assert f'window.{var}' in src, (
            f'startup.py does not initialise window.{var}. '
            f'Cross-IIFE cache variables must be on window.'
        )

    def test_no_bare_var_declarations_for_cache_vars(self):
        """No startup cache var should have a bare var declaration."""
        src = iife_src_file('src/visual/interactivity/startup.py')
        # Check none of the shared vars are declared with `var`
        for var in STARTUP_CACHE_VARS:
            assert f'var {var}' not in src, (
                f'startup.py declares var {var} — this traps it in the IIFE '
                f'local scope, making it invisible to all other panels.'
            )


# ---------------------------------------------------------------------------
# CONTRACT B — each consuming panel reads its cache var via window.*
# ---------------------------------------------------------------------------

class TestContractB_CacheConsumers:
    """Every panel that consumes a startup cache variable must use window.*.

    The consumer patterns are:
        if (window._xxx) { var cached = window._xxx; window._xxx = null; ... }

    ALL three parts are required:
        1. Read:    window._xxx
        2. Consume: window._xxx = null   (so re-open triggers fresh fetch)
    """

    # --- _tdPreloadDone ---

    def test_tradingdesk_reads_window_preload_done(self):
        """showPanel() must read window._tdPreloadDone, not bare _tdPreloadDone."""
        src = iife_src_file('src/visual/interactivity/trading/tradingdesk/panel_lifecycle.py')
        assert 'window._tdPreloadDone' in src, (
            'tradingdesk panel_lifecycle.py showPanel() must read window._tdPreloadDone. '
            'Bare _tdPreloadDone causes ReferenceError from a different IIFE.'
        )

    def test_preloader_sets_window_preload_done(self):
        """trading/preloader.py fallback must also set window._tdPreloadDone."""
        src = iife_src_file('src/visual/interactivity/trading/preloader.py')
        assert 'window._tdPreloadDone = true' in src

    def test_preloader_does_not_use_bare_td_preload_done_assignment(self):
        """preloader.py must not assign bare _tdPreloadDone (creates unreliable global)."""
        src = iife_src_file('src/visual/interactivity/trading/preloader.py')
        # Allow only window._ form — strip window. occurrences and check no bare assign remains
        bare_assigns = re.findall(r'(?<!window\.)_tdPreloadDone\s*=\s*true', src)
        assert not bare_assigns, (
            f'preloader.py has bare _tdPreloadDone = true assignment(s): {bare_assigns}. '
            f'Use window._tdPreloadDone = true for reliable cross-IIFE access.'
        )

    # --- _tdPreBlotter ---

    def test_blotter_reads_window_pre_blotter(self):
        src = iife_src_file('src/visual/interactivity/trading/blotter/setup.py')
        assert 'window._tdPreBlotter' in src

    def test_blotter_nulls_cache_after_consume(self):
        src = iife_src_file('src/visual/interactivity/trading/blotter/setup.py')
        assert 'window._tdPreBlotter = null' in src, (
            'blotter/setup.py must null window._tdPreBlotter after consuming so '
            'that a second open triggers a fresh fetch.'
        )

    # --- _tdPrePortStorms ---

    def test_port_stress_reads_window_pre_port_storms(self):
        src = iife_src_file('src/visual/interactivity/trading/port_stress/setup.py')
        assert 'window._tdPrePortStorms' in src

    def test_port_stress_nulls_cache_after_consume(self):
        src = iife_src_file('src/visual/interactivity/trading/port_stress/setup.py')
        assert 'window._tdPrePortStorms = null' in src

    # --- _preStorms ---

    def test_storm_portfolio_reads_window_pre_storms(self):
        src = iife_src_file('src/visual/interactivity/storm/sp_table.py')
        assert 'window._preStorms' in src

    def test_storm_portfolio_nulls_cache_after_consume(self):
        src = iife_src_file('src/visual/interactivity/storm/sp_table.py')
        assert 'window._preStorms = null' in src


# ---------------------------------------------------------------------------
# CONTRACT C — no panel may read a startup cache var without window.*
# ---------------------------------------------------------------------------

class TestContractC_NoBareReads:
    """No panel IIFE may read a startup-owned var without window. prefix.

    A bare read like ``if (_tdPreBlotter)`` inside a panel's own IIFE walks
    the scope chain: local → panel IIFE scope → global.  If startup.py set
    ``window._tdPreBlotter``, the global lookup succeeds.  BUT if startup.py
    ever reverts to ``var _tdPreBlotter``, the bare read silently gets
    ``undefined`` (or throws ReferenceError for the flag).  Requiring
    ``window.`` makes the intent explicit and the code robust to scoping changes.
    """

    def _check_no_bare_read(self, filepath: str, var: str) -> None:
        """Assert `var` is not read bare (without window.) in the given file."""
        src = iife_src_file(filepath)
        # Pattern: the var appears without window. prefix in an if/assignment context
        # We look for the var name NOT preceded by 'window.'
        # Use negative lookbehind: (?<!window\.)varname
        # Only flag actual reads/checks — not comments or string literals
        pattern = rf'(?<!window\.)(?<!\w){re.escape(var)}\b'
        # Find matches, ignoring comment lines and string-only lines
        lines = src.splitlines()
        bad_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            if re.search(pattern, line):
                # Exclude lines that are only the window.X = ... assignment form
                if f'window.{var}' not in line:
                    bad_lines.append((i, line.strip()))
        assert not bad_lines, (
            f'{filepath} has bare reads of {var} without window. prefix:\n'
            + '\n'.join(f'  L{ln}: {code}' for ln, code in bad_lines)
        )

    def test_tradingdesk_no_bare_preload_done(self):
        self._check_no_bare_read(
            'src/visual/interactivity/trading/tradingdesk/panel_lifecycle.py', '_tdPreloadDone')

    def test_preloader_no_bare_preload_done_read(self):
        """preloader.py checks should all use window._tdPreloadDone."""
        src = iife_src_file('src/visual/interactivity/trading/preloader.py')
        bad_lines = []
        for i, line in enumerate(src.splitlines(), 1):
            stripped = line.strip()
            # Skip Python comments, Python docstrings markers, and JS line comments
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            # Look for bare _tdPreloadDone that is NOT preceded by window.
            if re.search(r'(?<!window\.)(?<!\w)_tdPreloadDone\b', line):
                if 'window._tdPreloadDone' not in line:
                    bad_lines.append((i, stripped))
        assert not bad_lines, (
            f'preloader.py has bare reads of _tdPreloadDone outside comments:\n'
            + '\n'.join(f'  L{ln}: {code}' for ln, code in bad_lines)
        )

    def test_blotter_setup_no_bare_pre_blotter(self):
        self._check_no_bare_read(
            'src/visual/interactivity/trading/blotter/setup.py', '_tdPreBlotter')

    def test_port_stress_no_bare_pre_port_storms(self):
        self._check_no_bare_read(
            'src/visual/interactivity/trading/port_stress/setup.py', '_tdPrePortStorms')

    def test_storm_table_no_bare_pre_storms(self):
        self._check_no_bare_read(
            'src/visual/interactivity/storm/sp_table.py', '_preStorms')
