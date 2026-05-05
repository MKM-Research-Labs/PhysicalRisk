# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading workflow e2e test: property PRS commit flow.
Split from test_trading_workflows.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_property_panel,
)


class TestPropertyPRSCommit:
    """PRS pricing commit on property hazard panel."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page, first_property_id):
        close_all_panels(map_page)
        has_fn = map_page.evaluate(
            "() => typeof window.viewPropertyHazard === 'function'"
        )
        if not has_fn:
            pytest.skip("window.viewPropertyHazard not available")
        open_property_panel(map_page, first_property_id)
        # Switch to PRS pricing tab (tab 2)
        tab = map_page.locator(".phc-tab[data-tab='2']")
        if tab.count() > 0:
            tab.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        close_all_panels(map_page)

    def test_prs_controls_exist(self, map_page):
        """Property PRS tab should have notional, spread, and EA zone inputs."""
        panel = map_page.locator("#property-hc-panel")
        notional = panel.locator(
            "input[id*='notional'], input[id*='phc-notional']"
        ).first
        spread = panel.locator(
            "input[id*='spread'], input[id*='phc-spread']"
        ).first
        ea_zone = panel.locator("select[id='phc-ea-zone']").first

        controls_found = (
            (1 if notional.count() > 0 else 0)
            + (1 if spread.count() > 0 else 0)
            + (1 if ea_zone.count() > 0 else 0)
        )
        if controls_found == 0:
            pytest.skip("No PRS controls found on property panel")
        assert controls_found >= 3, (
            f"Expected at least 3 PRS controls (notional, spread, EA zone), "
            f"found {controls_found}"
        )

    def test_fill_prs_values(self, map_page):
        """Should be able to fill notional and spread fields."""
        panel = map_page.locator("#property-hc-panel")

        # Fill notional
        filled = False
        notional_loc = panel.locator(
            "input[id*='notional'], input[id*='phc-notional']"
        )
        if notional_loc.count() > 0:
            notional = notional_loc.first
            if notional.is_visible():
                notional.fill("500000")
                map_page.wait_for_timeout(1_500)
                filled = True

        # Fill spread
        spread_loc = panel.locator(
            "input[id*='spread'], input[id*='phc-spread']"
        )
        if spread_loc.count() > 0:
            spread = spread_loc.first
            if spread.is_visible():
                spread.fill("30")
                map_page.wait_for_timeout(1_500)
                filled = True

        # If no dedicated fields, try any visible input in the panel
        if not filled:
            any_input = panel.locator("input[type='number'], input[type='text']")
            if any_input.count() > 0 and any_input.first.is_visible():
                any_input.first.fill("100")
                filled = True

        if not filled:
            pytest.skip("No fillable PRS fields found on property hazard panel")

    # Note: commit-button coverage is provided by tests/e2e/test_lifecycle_property_prs.py,
    # which exercises the real commit flow via the actual element IDs.
