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
