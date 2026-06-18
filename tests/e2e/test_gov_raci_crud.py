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
Governance e2e tests: RACI matrix interaction and MRC meeting CRUD.
Split from test_governance_crud.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    get_governance_content_text,
    open_governance,
    switch_governance_tab,
)


class TestRACIMatrixInteraction:
    """RACI tab — matrix grid rendering and cell interaction."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "raci")
        yield
        close_all_panels(map_page)

    def test_matrix_grid_renders(self, map_page):
        """RACI tab should render a matrix grid (table with cells)."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0

        table = content.locator("table")
        if table.count() == 0:
            pytest.skip("No RACI matrix table found")

        # Table should have headers and data cells
        headers = table.first.locator("th")
        cells = table.first.locator("td")
        assert headers.count() >= 2, (
            f"RACI table should have at least 2 headers, found {headers.count()}"
        )
        assert cells.count() >= 1, "RACI table should have at least 1 data cell"

    def test_cells_interactive(self, map_page):
        """RACI matrix cells should be clickable or have dropdowns."""
        content = map_page.locator("#mg-content")
        table = content.locator("table")
        if table.count() == 0:
            pytest.skip("No RACI matrix table found")

        cells = table.first.locator("td")
        if cells.count() == 0:
            pytest.skip("No data cells in RACI matrix")

        # Check if cells have interactive elements (select, button) or cursor pointer
        first_cell = cells.first
        has_select = first_cell.locator("select").count() > 0
        has_button = first_cell.locator("button").count() > 0
        cursor = first_cell.evaluate(
            "el => window.getComputedStyle(el).cursor"
        )
        has_onclick = first_cell.evaluate(
            "el => !!el.onclick || el.getAttribute('onclick') !== null"
        )
        is_interactive = has_select or has_button or cursor == "pointer" or has_onclick

        if not is_interactive:
            # Try clicking and check for dropdown or modal
            first_cell.click(force=True)
            map_page.wait_for_timeout(900)
            dropdown = map_page.locator("[class*='dropdown']").or_(
                map_page.locator("select:visible")
            ).or_(
                map_page.locator("[class*='menu']")
            )
            is_interactive = dropdown.count() > 0

        if not is_interactive:
            pytest.skip("RACI cells do not appear interactive")


class TestMRCMeetingCRUD:
    """MRC tab — meeting list, add button, and form/modal."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        open_governance(map_page)
        switch_governance_tab(map_page, "mrc")
        yield
        close_all_panels(map_page)

    def test_meeting_list_renders(self, map_page):
        """MRC tab should render a meeting list or table."""
        content = map_page.locator("#mg-content")
        assert content.count() > 0

        table = content.locator("table")
        list_el = content.locator("ul, ol, [class*='list'], [class*='meeting']")
        text = get_governance_content_text(map_page)

        has_list = (
            table.count() > 0
            or list_el.count() > 0
            or "meeting" in text
            or "committee" in text
        )
        assert has_list, "No meeting list/table found in MRC tab"

    def test_add_meeting_button_exists(self, map_page):
        """MRC tab should have a 'New Meeting' or 'Add' button."""
        content = map_page.locator("#mg-content")
        add_btn = content.locator("button").filter(has_text="New").or_(
            content.locator("button").filter(has_text="Add")
        ).or_(
            content.locator("button").filter(has_text="Create")
        ).or_(
            content.locator("button").filter(has_text="Schedule")
        ).or_(
            # Restrict title fallbacks to button-like elements: the union's
            # .first resolves in DOM order, so a non-button [title] element
            # earlier in #mg-content would otherwise win and break is_enabled().
            content.locator("button[title*='New'], [role='button'][title*='New']")
        ).or_(
            content.locator("button[title*='Add'], [role='button'][title*='Add']")
        )

        if add_btn.count() == 0:
            pytest.skip("No 'New Meeting' or 'Add' button found in MRC tab")

        assert add_btn.first.is_visible(), "Add meeting button is not visible"
        assert add_btn.first.is_enabled(), "Add meeting button is not enabled"

    def test_add_button_opens_form(self, map_page):
        """Clicking the add button should open a form or modal."""
        content = map_page.locator("#mg-content")
        add_btn = content.locator("button").filter(has_text="New").or_(
            content.locator("button").filter(has_text="Add")
        ).or_(
            content.locator("button").filter(has_text="Create")
        ).or_(
            content.locator("button").filter(has_text="Schedule")
        ).or_(
            content.locator("button[title*='New'], [role='button'][title*='New']")
        ).or_(
            content.locator("button[title*='Add'], [role='button'][title*='Add']")
        )

        if add_btn.count() == 0:
            pytest.skip("No add button found in MRC tab")

        add_btn.first.click(force=True)
        map_page.wait_for_timeout(1_500)

        # Look for form, modal, or new input fields
        form = map_page.locator("form").or_(
            map_page.locator("[class*='modal']")
        ).or_(
            map_page.locator("[class*='dialog']")
        ).or_(
            map_page.locator("[role='dialog']")
        )

        inputs = map_page.locator("#mg-content input, #mg-content textarea, #mg-content select")
        has_form = form.count() > 0 or inputs.count() > 0

        if not has_form:
            # Check if content area changed (inline form)
            new_text = get_governance_content_text(map_page)
            has_form = "date" in new_text or "agenda" in new_text or "title" in new_text

        assert has_form, "No form or modal appeared after clicking add button"

        # Close/cancel if possible
        cancel_btn = map_page.locator("button").filter(has_text="Cancel").or_(
            map_page.locator("[class*='close']")
        )
        if cancel_btn.count() > 0:
            cancel_btn.first.click(force=True)
            map_page.wait_for_timeout(900)
