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
JS safety tests for governance get_js() modules — part 1.

Covers: TestGetJsReturnsString, TestNoLiteralNewlineInJsStrings,
TestFullCompilation.
"""

import re
import subprocess
import tempfile
import os

import pytest

from tests.visual.governance.conftest import js_string_newline_offenders


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
    is a SyntaxError.  The browser silently drops the entire script block.
    """

    def test_audit_reports_no_newline_in_js_strings(self, audit_reports_js):
        offenders = js_string_newline_offenders(audit_reports_js)
        assert offenders == [], (
            "mg_audit_reports.get_js() contains JS string literal(s) with a "
            "bare newline -- use '\\\\n' in the Python source instead of '\\n':\n"
            + "\n".join(repr(o) for o in offenders)
        )

    def test_all_modules_no_newline_in_js_strings(self, all_governance_js):
        failures = {}
        for name, js in all_governance_js.items():
            offenders = js_string_newline_offenders(js)
            if offenders:
                failures[name] = offenders
        assert failures == {}, (
            "Bare newlines found in JS string literals -- use '\\\\n' not '\\n':\n"
            + "\n".join(
                f"  {name}: {offenders}"
                for name, offenders in failures.items()
            )
        )

    def test_full_compiled_js_no_newline_in_js_strings(self, full_governance_js):
        offenders = js_string_newline_offenders(full_governance_js)
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
        """Run node --check on the compiled governance script."""
        node = subprocess.run(['which', 'node'], capture_output=True, text=True)
        if node.returncode != 0:
            pytest.skip('node not available -- install Node.js to enable this check')

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
