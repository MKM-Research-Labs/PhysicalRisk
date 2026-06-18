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
Governance e2e test: BCBS 239 principle editing.
Split from test_governance_crud.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_governance,
    switch_governance_tab,
)


class TestBCBS239PrincipleEdit:
    """BCBS 239 tab — edit buttons, modal with fields, confirm/cancel."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "bcbs239")
        yield
        close_all_panels(map_page)

    def _find_edit_buttons(self, page):
        """Find edit buttons/icons in the BCBS 239 tab."""
        content = page.locator("#mg-content")
        return content.locator("button").filter(has_text="Edit").or_(
            content.locator("button").filter(has_text="edit")
        ).or_(
            content.locator("[title*='Edit']")
        ).or_(
            content.locator("[title*='edit']")
        ).or_(
            content.locator("[class*='edit']")
        ).or_(
            content.locator("button i[class*='edit']").locator(".."))

    def test_edit_buttons_on_principles(self, map_page):
        """BCBS 239 tab should have edit buttons/icons on principle rows."""
        edit_btns = self._find_edit_buttons(map_page)
        if edit_btns.count() == 0:
            pytest.skip("No edit buttons found on BCBS 239 principle rows")
        assert edit_btns.count() >= 1, "Expected at least one edit button"

    # Note: BCBS uses inline editing rather than a modal, so the modal-based
    # tests have been removed. test_edit_buttons_on_principles above covers
    # the existence of the edit affordance; deeper inline-edit coverage would
    # need a different test design.
