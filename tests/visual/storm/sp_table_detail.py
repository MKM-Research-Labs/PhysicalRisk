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
Regression tests for sp_table.py (Storm Portfolio — Table tab sub-module).

Snag 2/4 regression: the Portfolio Storm Impact panel title must display the
full storm label (name + storm_id) taken from the dropdown's selected option,
NOT the bare storm_id string.  The old code appended just `stormId` to the
title which, when storm.name was empty, produced "Storm ID (Storm ID)".
"""

import pytest


@pytest.fixture(scope='module')
def table_js():
    from visual.interactivity.storm import sp_table
    return sp_table.get_js()


# ---------------------------------------------------------------------------
# Panel title label (Snag 2 / Snag 4 regression)
# ---------------------------------------------------------------------------

class TestPanelTitle:
    """Panel title must use the dropdown's display text, not the raw storm ID."""

    def test_title_reads_selected_option_text(self, table_js):
        """Panel title must use options[selectedIndex].textContent.

        Regression: old code appended just `stormId` which, when storm.name='',
        produced 'STORM-xxxx (STORM-xxxx)' instead of 'Moderate 20mm (STORM-xxxx)'.
        """
        assert 'selectedIndex' in table_js, (
            "Panel title must read the selected option's text via selectedIndex"
        )
        assert 'textContent' in table_js, (
            "Panel title must use .textContent to get the formatted storm label"
        )

    def test_panel_title_id_present(self, table_js):
        """sp-panel-title element ID must be referenced in the JS."""
        assert 'sp-panel-title' in table_js

    def test_panel_title_prefix(self, table_js):
        """Title must start with 'Portfolio Storm Impact'."""
        assert 'Portfolio Storm Impact' in table_js

    def test_title_uses_label_variable_not_bare_storm_id_concat(self, table_js):
        """Title assignment must NOT directly concatenate bare stormId.

        Regression guard: the buggy pattern was:
          .textContent = 'Portfolio Storm Impact — ' + stormId
        The fix introduces a label variable read from the dropdown.
        """
        # The fixed version uses a label variable (e.g. _stormLabel) so the
        # bare 'stormId' should NOT be the final token in the title assignment.
        assert "Portfolio Storm Impact \\u2014 ' + stormId" not in table_js, (
            "Title must NOT use bare stormId — that causes 'ID (ID)' when "
            "storm name is empty.  Use the dropdown's selected option text."
        )


# ---------------------------------------------------------------------------
# Storm list loading
# ---------------------------------------------------------------------------

class TestStormListLoading:
    """Storm list must be loaded from the correct endpoint."""

    def test_loads_from_propertyts_storms(self, table_js):
        """Storm list endpoint must be /api/v1/propertyts/storms."""
        assert '/api/v1/propertyts/storms' in table_js

    def test_uses_preloaded_cache(self, table_js):
        """JS must check window._preStorms cache before fetching."""
        assert '_preStorms' in table_js

    def test_no_storms_message(self, table_js):
        """Empty storm list must display a user-readable message."""
        assert 'No flooding storms found' in table_js


# ---------------------------------------------------------------------------
# Table structure
# ---------------------------------------------------------------------------

class TestTableStructure:
    """Sortable property damage table must be fully specified."""

    def test_load_portfolio_impact_defined(self, table_js):
        """loadPortfolioImpact() must be defined."""
        assert 'loadPortfolioImpact' in table_js

    def test_portfolio_impact_endpoint(self, table_js):
        """Portfolio impact fetch must use the correct endpoint path."""
        assert 'portfolio-impact' in table_js

    def test_summary_cards_present(self, table_js):
        """Summary card labels must be present."""
        assert 'Properties Affected' in table_js
        assert 'Total Flood Damage' in table_js

    def test_sort_columns_defined(self, table_js):
        """Sort state variables must be initialised."""
        assert 'spSortCol' in table_js
        assert 'spSortAsc' in table_js


# ---------------------------------------------------------------------------
# Storm list sort mode support
# ---------------------------------------------------------------------------

class TestStormListSortMode:
    """loadStormList must accept a sortMode parameter and pass it to the API."""

    def test_load_storm_list_accepts_sort_mode(self, table_js):
        """loadStormList should accept sortMode parameter."""
        assert 'function loadStormList(sortMode)' in table_js

    def test_sort_mode_passed_to_api(self, table_js):
        """sortMode must be appended to the API URL as ?sort= parameter."""
        assert '?sort=' in table_js

    def test_data_total_attribute_set(self, table_js):
        """Storm select must store total catalogue count in data-total."""
        assert 'data-total' in table_js
        assert 'total_storms' in table_js

    def test_default_sort_is_damage(self, table_js):
        """Default sortMode must be 'damage'."""
        assert "sortMode || 'damage'" in table_js or \
               "sortMode = sortMode || 'damage'" in table_js
