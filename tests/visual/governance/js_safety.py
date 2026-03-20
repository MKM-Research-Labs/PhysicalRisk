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
JS safety tests for all governance get_js() modules.

These tests catch the two recurring bugs:

  1. Literal newlines inside JavaScript string literals.
     In Python triple-quoted strings, '\n' is a real newline.  When that
     string is embedded in HTML, the browser JS parser sees a string literal
     spanning a line — which is a SyntaxError.  The whole IIFE fails silently
     and UI buttons (e.g. the Regulatory shield) disappear.

     Fix: use '\\n' in Python source so the output JS contains the two-char
     escape sequence '\n', not a raw newline character.

  2. Unescaped single quotes inside JS single-quoted string literals.
     In a Python triple-quoted string, \'  resolves to just ' (no backslash).
     When that ' appears inside a JS string delimited by ', it terminates the
     string early, causing a SyntaxError.  The whole IIFE fails silently.

     Fix: use \\' in Python source so the output JS contains \' (escaped quote).

  3. Unescaped braces in f-strings.
     Any literal '{' or '}' inside a Python f-string must be doubled.
     Un-doubled braces cause a NameError (or KeyError) at render time which
     again silently breaks all subsequent <script> blocks.

Run after ANY change to a get_js() module — the test suite must catch these
before the visual is regenerated.
"""

import re
import subprocess
import tempfile
import os
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _js_string_newline_offenders(js: str) -> list[str]:
    """
    Return JS string literals that contain a bare newline.

    Detects the specific bug pattern where Python '\n' (real newline char)
    ends up inside a JS single-quoted string literal, producing a
    SyntaxError in the browser.

    We check for:
      1. An empty/whitespace-only JS string spanning a line break:
            '[ \t]*\n[ \t]*'     e.g.  .join('<newline>')
      2. A non-empty JS string argument where the content before the
         newline is preceded by ( or , (common argument context):
            (param, '...<newline>...')

    False-positive avoidance: we do NOT match closing-quote + newline +
    opening-quote of two separate statements (like `'val';\n  var x = '`)
    because those have non-whitespace chars between the quotes.
    """
    hits = []

    # Pattern 1: string contains ONLY whitespace + newline + whitespace
    # (catches join('\n'), split('\n'), etc.)
    hits.extend(re.findall(r"'[ \t]*\n[ \t]*'", js))

    # Pattern 2: string opens after ( or , or =, has content, then newline
    # Catches: func('text\nmore text') cases
    hits.extend(re.findall(r"(?<=[\(,=])\s*'[^'\n\\]*\n[^']*'", js))

    return hits


def _collect_all_governance_js() -> dict[str, str]:
    """Import every governance get_js() module and return {name: js}."""
    from visual.interactivity.governance import (
        mg_audit,
        mg_audit_reports,
        mg_bibliography,
        mg_documents,
        mg_edit_modal,
        mg_helpers,
        mg_panel_ui,
    )
    from visual.interactivity.governance.models import (
        mg_bcbs239,
        mg_chain,
        mg_detail_header,
        mg_detail_tabs,
        mg_inventory,
        mg_validation,
    )
    from visual.interactivity.governance.mrc import mg_mrc, mg_mrc_meeting
    from visual.interactivity.governance.raci import mg_raci

    modules = {
        'mg_audit':          mg_audit,
        'mg_audit_reports':  mg_audit_reports,
        'mg_bibliography':   mg_bibliography,
        'mg_documents':      mg_documents,
        'mg_edit_modal':     mg_edit_modal,
        'mg_helpers':        mg_helpers,
        'mg_panel_ui':       mg_panel_ui,
        'mg_bcbs239':        mg_bcbs239,
        'mg_chain':          mg_chain,
        'mg_detail_header':  mg_detail_header,
        'mg_detail_tabs':    mg_detail_tabs,
        'mg_inventory':      mg_inventory,
        'mg_validation':     mg_validation,
        'mg_mrc':            mg_mrc,
        'mg_mrc_meeting':    mg_mrc_meeting,
        'mg_raci':           mg_raci,
    }
    return {name: mod.get_js() for name, mod in modules.items()}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def all_governance_js():
    return _collect_all_governance_js()


@pytest.fixture(scope='module')
def audit_reports_js():
    from visual.interactivity.governance import mg_audit_reports
    return mg_audit_reports.get_js()


@pytest.fixture(scope='module')
def full_governance_js():
    """Full compiled JS from ModelGovernancePanel.get_js() — exercises the
    f-string assembly and all sub-module embedding in one shot."""
    from visual.interactivity.governance.modelgovernance import ModelGovernancePanel
    panel = ModelGovernancePanel()
    return panel.get_js()


# ---------------------------------------------------------------------------
# Safety: every module returns a non-empty string
# ---------------------------------------------------------------------------

class TestGetJsReturnsString:

    def test_all_modules_return_str(self, all_governance_js):
        for name, js in all_governance_js.items():
            assert isinstance(js, str), f"{name}.get_js() did not return str"

    def test_all_modules_non_empty(self, all_governance_js):
        for name, js in all_governance_js.items():
            assert len(js) > 50, f"{name}.get_js() returned suspiciously short string"


# ---------------------------------------------------------------------------
# Safety: no literal newlines inside JS string literals
# ---------------------------------------------------------------------------

class TestNoLiteralNewlineInJsStrings:
    """
    Regression guard for the 'Regulatory button disappears' bug.

    A real newline character inside a JavaScript single-quoted string literal
    is a SyntaxError.  The browser silently drops the entire script block,
    which means the Leaflet control that adds the Regulatory button never runs.
    """

    def test_audit_reports_no_newline_in_js_strings(self, audit_reports_js):
        offenders = _js_string_newline_offenders(audit_reports_js)
        assert offenders == [], (
            "mg_audit_reports.get_js() contains JS string literal(s) with a "
            "bare newline — use '\\\\n' in the Python source instead of '\\n':\n"
            + "\n".join(repr(o) for o in offenders)
        )

    def test_all_modules_no_newline_in_js_strings(self, all_governance_js):
        failures = {}
        for name, js in all_governance_js.items():
            offenders = _js_string_newline_offenders(js)
            if offenders:
                failures[name] = offenders
        assert failures == {}, (
            "Bare newlines found in JS string literals — use '\\\\n' not '\\n':\n"
            + "\n".join(
                f"  {name}: {offenders}"
                for name, offenders in failures.items()
            )
        )

    def test_full_compiled_js_no_newline_in_js_strings(self, full_governance_js):
        offenders = _js_string_newline_offenders(full_governance_js)
        assert offenders == [], (
            "Full compiled governance JS contains JS string literal(s) with a "
            "bare newline:\n" + "\n".join(repr(o) for o in offenders)
        )


# ---------------------------------------------------------------------------
# Safety: full compiled JS assembles without Python errors
# ---------------------------------------------------------------------------

class TestFullCompilation:

    def test_full_js_is_str(self, full_governance_js):
        assert isinstance(full_governance_js, str)

    def test_full_js_non_empty(self, full_governance_js):
        assert len(full_governance_js) > 10_000

    def test_full_js_contains_script_tags(self, full_governance_js):
        assert '<script>' in full_governance_js
        assert '</script>' in full_governance_js

    def test_full_js_contains_regulatory_button(self, full_governance_js):
        """The Leaflet control that adds the Regulatory shield must be present."""
        assert 'GovernanceControl' in full_governance_js
        assert 'Regulatory Compliance' in full_governance_js

    def test_full_js_contains_iife(self, full_governance_js):
        assert '(function()' in full_governance_js or '(function ()' in full_governance_js

    def test_full_js_contains_show_mg_panel(self, full_governance_js):
        assert 'showMgPanel' in full_governance_js

    def test_full_js_contains_terminal_popup(self, full_governance_js):
        """Terminal popup added in last session must be present."""
        assert '_openTerminalPopup' in full_governance_js
        assert '_auditTerminalRefreshNow' in full_governance_js

    def test_full_js_contains_render_audit_reports(self, full_governance_js):
        assert 'renderAuditReports' in full_governance_js

    def test_full_js_passes_node_syntax_check(self, full_governance_js):
        """Run node --check on the compiled governance script.

        This is the definitive guard: it catches ALL JS syntax errors
        (unescaped quotes, literal newlines in strings, mismatched braces, etc.)
        that the regex-based checks might miss.
        """
        node = subprocess.run(['which', 'node'], capture_output=True, text=True)
        if node.returncode != 0:
            pytest.skip('node not available — install Node.js to enable this check')

        # Extract just the script content (strip <script> tags)
        script = re.sub(r'</?script[^>]*>', '', full_governance_js).strip()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script)
            tmp = f.name
        try:
            result = subprocess.run(
                ['node', '--check', tmp],
                capture_output=True, text=True, timeout=15
            )
            assert result.returncode == 0, (
                'Governance JS failed node --check (SyntaxError):\n' + result.stderr[:1000]
            )
        finally:
            os.unlink(tmp)


# ---------------------------------------------------------------------------
# Audit reports content checks
# ---------------------------------------------------------------------------

class TestAuditReportsContent:

    def test_run_test_suite_function(self, audit_reports_js):
        assert '_runTestSuite' in audit_reports_js

    def test_terminal_overlay_id(self, audit_reports_js):
        assert '_audit-terminal-overlay' in audit_reports_js

    def test_poll_output_endpoint(self, audit_reports_js):
        assert 'test-report/output' in audit_reports_js

    def test_no_json_download_button(self, audit_reports_js):
        """JSON button was deliberately removed — must not reappear."""
        assert 'test_failures_report.json' not in audit_reports_js

    def test_refresh_audit_tab_button(self, audit_reports_js):
        assert '_auditTerminalRefreshNow' in audit_reports_js

    def test_run_test_suite_exposed_on_window(self, audit_reports_js):
        """_runTestSuite must be on window — onclick attributes execute in global scope."""
        assert 'window._runTestSuite' in audit_reports_js

    def test_toggle_failure_detail_exposed_on_window(self, audit_reports_js):
        """_toggleFailureDetail must be on window — called from onclick in innerHTML."""
        assert 'window._toggleFailureDetail' in audit_reports_js

    def test_audit_terminal_refresh_exposed_on_window(self, audit_reports_js):
        """_auditTerminalRefreshNow must be on window — called from onclick in innerHTML."""
        assert 'window._auditTerminalRefreshNow' in audit_reports_js
