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
JS safety tests for governance get_js() modules — part 2.

Covers: TestAuditReportsContent.
"""

import pytest


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
        """JSON button was deliberately removed -- must not reappear."""
        assert 'test_failures_report.json' not in audit_reports_js

    def test_refresh_audit_tab_button(self, audit_reports_js):
        assert '_auditTerminalRefreshNow' in audit_reports_js

    def test_run_test_suite_exposed_on_window(self, audit_reports_js):
        """_runTestSuite must be on window -- onclick attributes execute in global scope."""
        assert 'window._runTestSuite' in audit_reports_js

    def test_toggle_failure_detail_exposed_on_window(self, audit_reports_js):
        """_toggleFailureDetail must be on window -- called from onclick in innerHTML."""
        assert 'window._toggleFailureDetail' in audit_reports_js

    def test_audit_terminal_refresh_exposed_on_window(self, audit_reports_js):
        """_auditTerminalRefreshNow must be on window -- called from onclick in innerHTML."""
        assert 'window._auditTerminalRefreshNow' in audit_reports_js
