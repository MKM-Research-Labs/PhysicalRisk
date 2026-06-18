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
Governance e2e tests: MRC CRUD sub-routes — part 2.

Covers decisions and actions CRUD via API.
"""

import pytest

from tests.e2e.conftest import get_first_meeting_id


# ---------------------------------------------------------------------------
# Decisions CRUD API
# ---------------------------------------------------------------------------


class TestMRCDecisionsCRUD:
    """Decisions CRUD via API."""

    def test_add_decision(self, map_page):
        """POST decision should auto-generate ID and save."""
        meeting_id = get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/decisions',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        description: 'E2E test decision',
                        date: '2026-03-24'
                    }})
                }}
            );
            var data = await resp.json();
            var decisions = (data.meeting || {{}}).decisions || [];
            var last = decisions[decisions.length - 1] || {{}};
            return {{
                http_status: resp.status,
                api_status: data.status,
                has_id: !!last.id,
                id_format: (last.id || '').substring(0, 2),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["has_id"], "Decision missing auto-generated ID"
        assert result["id_format"] == "D-", \
            f"Expected D-xxx format, got {result['id_format']}"

    def test_delete_decision(self, map_page):
        """DELETE decision should succeed."""
        meeting_id = get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var decisions = (data1.meeting || {{}}).decisions || [];
            if (decisions.length === 0) return {{ skip: true }};
            var lastId = decisions[decisions.length - 1].id;
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/decisions/' + lastId + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No decisions to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"


# ---------------------------------------------------------------------------
# Actions CRUD API
# ---------------------------------------------------------------------------


class TestMRCActionsCRUD:
    """Actions CRUD via API."""

    def test_add_action(self, map_page):
        """POST action should auto-generate ID and save."""
        meeting_id = get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/actions',
                {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        description: 'E2E test action item',
                        owner: 'Test User',
                        target_date: '2026-04-24',
                        status: 'Open'
                    }})
                }}
            );
            var data = await resp.json();
            var actions = (data.meeting || {{}}).actions || [];
            var last = actions[actions.length - 1] || {{}};
            return {{
                http_status: resp.status,
                api_status: data.status,
                has_id: !!last.id,
                id_format: (last.id || '').substring(0, 2),
            }};
        }}""")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
        assert result["has_id"], "Action missing auto-generated ID"
        assert result["id_format"] == "A-", \
            f"Expected A-xxx format, got {result['id_format']}"

    def test_delete_action(self, map_page):
        """DELETE action should succeed."""
        meeting_id = get_first_meeting_id(map_page)
        if not meeting_id:
            pytest.skip("No meetings available")

        result = map_page.evaluate(f"""async () => {{
            var cfg = window.__BACKEND_CONFIG || {{}};
            var baseUrl = cfg.url || '';
            var resp1 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}'
            );
            var data1 = await resp1.json();
            var actions = (data1.meeting || {{}}).actions || [];
            if (actions.length === 0) return {{ skip: true }};
            var lastId = actions[actions.length - 1].id;
            var resp2 = await fetch(
                baseUrl + '/api/v1/governance/mrc/meetings/{meeting_id}/actions/' + lastId + '/delete',
                {{ method: 'POST' }}
            );
            var data2 = await resp2.json();
            return {{
                http_status: resp2.status,
                api_status: data2.status,
            }};
        }}""")
        if result.get("skip"):
            pytest.skip("No actions to delete")
        assert result["http_status"] == 200
        assert result["api_status"] == "success"
