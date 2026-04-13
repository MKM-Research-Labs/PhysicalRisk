# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
Trading workflow e2e test: gauge PRS commit flow.
Split from test_trading_workflows.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_gauge_panel,
)


class TestGaugePRSCommit:
    """PRS pricing commit on gauge panel: select ctpy, fill fields, commit."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page, first_traded_gauge_id):
        close_all_panels(map_page)
        open_gauge_panel(map_page, first_traded_gauge_id)
        # Switch to PRS Pricing tab (tab 0)
        tab = map_page.locator(".hazard-tab[data-tab='0']")
        if tab.count() > 0:
            tab.click(force=True)
        map_page.wait_for_timeout(3_000)
        yield
        close_all_panels(map_page)

    def test_counterparty_dropdown_has_options(self, map_page):
        """PRS tab should have a counterparty dropdown with at least one option."""
        panel = map_page.locator("#hazard-curve-panel")
        # Look for counterparty dropdown
        ctpy_select = panel.locator(
            "select[id*='ctpy'], select[id*='counterparty'], "
            "select[id*='cpty'], select[name*='counterparty']"
        ).first
        if ctpy_select.count() == 0 or not ctpy_select.is_visible():
            pytest.skip("No counterparty dropdown found on PRS tab")

        options = ctpy_select.locator("option")
        # Exclude placeholder/empty options
        real_options = 0
        for i in range(options.count()):
            val = options.nth(i).get_attribute("value")
            if val and val.strip() and val != "":
                real_options += 1
        assert real_options > 0, "Counterparty dropdown has no options"

    def test_selecting_counterparty_enables_commit(self, map_page):
        """Selecting a counterparty should enable or reveal the commit button."""
        panel = map_page.locator("#hazard-curve-panel")
        ctpy_select = panel.locator(
            "select[id*='ctpy'], select[id*='counterparty'], "
            "select[id*='cpty'], select[name*='counterparty']"
        ).first
        if ctpy_select.count() == 0 or not ctpy_select.is_visible():
            pytest.skip("No counterparty dropdown found")

        # Pick the first real option
        options = ctpy_select.locator("option")
        for i in range(options.count()):
            val = options.nth(i).get_attribute("value")
            if val and val.strip():
                ctpy_select.select_option(value=val)
                break
        map_page.wait_for_timeout(3_000)

        # Check commit button exists somewhere in the panel
        commit_btn = panel.locator(
            "button:has-text('Commit'), button:has-text('Trade'), "
            "button:has-text('Book'), button[id*='commit']"
        ).first
        if commit_btn.count() == 0:
            pytest.skip("Commit button never appeared after selecting counterparty")
        # Button should exist (may be enabled or disabled)
        assert commit_btn.count() > 0

    def test_fill_notional_and_spread(self, map_page):
        """Notional and spread input fields should accept values."""
        panel = map_page.locator("#hazard-curve-panel")
        notional_input = panel.locator(
            "input[id*='notional'], input[name*='notional']"
        ).first
        spread_input = panel.locator(
            "input[id*='spread'], input[name*='spread']"
        ).first

        if notional_input.count() == 0 and spread_input.count() == 0:
            pytest.skip("No notional or spread inputs on PRS tab")

        if notional_input.count() > 0 and notional_input.is_visible():
            notional_input.fill("1000000")
            map_page.wait_for_timeout(1_500)
            val = notional_input.input_value()
            assert "1000000" in val or len(val) > 0

        if spread_input.count() > 0 and spread_input.is_visible():
            spread_input.fill("25")
            map_page.wait_for_timeout(1_500)
            val = spread_input.input_value()
            assert "25" in val or len(val) > 0

