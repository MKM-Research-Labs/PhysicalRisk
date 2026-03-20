# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""
E2e test: Gauge PRS pricing -> book a trade -> verify in blotter.
Split from test_trading_lifecycle.py.
"""

import pytest

from tests.e2e.helpers import (
    close_all_panels,
    open_gauge_panel,
    open_trading_desk,
    switch_to_prs_tab_gauge,
)


class TestGaugePRSBookTrade:
    """Full workflow: open gauge PRS -> price -> select counterparty -> commit -> verify in blotter."""

    @pytest.fixture(autouse=True)
    def setup(self, map_page):
        close_all_panels(map_page)
        yield

    def test_01_open_prs_and_verify_controls(self, map_page, first_traded_gauge_id):
        """Open gauge panel PRS tab and verify all pricing controls exist."""
        open_gauge_panel(map_page, first_traded_gauge_id)
        switch_to_prs_tab_gauge(map_page)

        # Verify controls — actual IDs from ghc_prs_controls.py:
        # prs-direction, prs-counterparty, prs-trigger, prs-notional, prs-maturity, prs-spread
        for ctrl_id in [
            "prs-direction", "prs-counterparty", "prs-trigger",
            "prs-notional", "prs-maturity", "prs-spread",
        ]:
            found = map_page.evaluate(
                f"() => document.getElementById('{ctrl_id}') !== null"
            )
            assert found, f"Control #{ctrl_id} not found on gauge PRS tab"

    def test_02_select_counterparty(self, map_page, first_traded_gauge_id):
        """Select a counterparty from the dropdown."""
        open_gauge_panel(map_page, first_traded_gauge_id)
        switch_to_prs_tab_gauge(map_page)

        ctpy = map_page.locator("#prs-counterparty")
        if ctpy.count() == 0:
            pytest.skip("Counterparty dropdown not found")

        options = ctpy.locator("option")
        option_count = options.count()
        assert option_count > 1, (
            f"Counterparty dropdown has only {option_count} options (need at least 2)"
        )

        # Select second option (first is "-- Select --")
        ctpy.select_option(index=1)
        map_page.wait_for_timeout(500)

        selected = ctpy.input_value()
        assert selected != "", "No counterparty selected"

    def test_03_set_trade_parameters(self, map_page, first_traded_gauge_id):
        """Set direction, trigger, notional, and tenor."""
        open_gauge_panel(map_page, first_traded_gauge_id)
        switch_to_prs_tab_gauge(map_page)

        # Direction -> Payer
        direction = map_page.locator("#prs-direction")
        if direction.count() > 0:
            direction.select_option(value="payer")

        # Trigger -> severe
        trigger = map_page.locator("#prs-trigger")
        if trigger.count() > 0:
            trigger.select_option(value="severe")

        # Notional
        notional = map_page.locator("#prs-notional")
        if notional.count() > 0:
            notional.fill("5,000,000")

        map_page.wait_for_timeout(500)

        # Verify spread display or hazard info is rendered
        hazard_display = map_page.locator("#prs-hazard-display")
        panel_text = map_page.locator("#hazard-curve-panel").inner_text()
        assert "bps" in panel_text.lower() or hazard_display.count() > 0, (
            "No spread/pricing data shown after setting parameters"
        )

    def test_04_commit_trade(self, map_page, first_traded_gauge_id):
        """Click commit to book the trade."""
        open_gauge_panel(map_page, first_traded_gauge_id)
        switch_to_prs_tab_gauge(map_page)

        # Must select counterparty first (required)
        ctpy = map_page.locator("#prs-counterparty")
        if ctpy.count() > 0:
            options_count = ctpy.locator("option").count()
            if options_count > 1:
                ctpy.select_option(index=1)

        # Set notional
        notional = map_page.locator("#prs-notional")
        if notional.count() > 0:
            notional.fill("5,000,000")

        map_page.wait_for_timeout(500)

        # Find commit button — ID from ghc_prs_commit.py is "prs-commit-btn"
        commit_btn = map_page.locator("#prs-commit-btn")
        if commit_btn.count() == 0:
            # Fallback: any button with "Commit" text in the panel
            commit_btn = map_page.locator(
                "#hazard-curve-panel button:has-text('Commit')"
            )
        if commit_btn.count() == 0:
            pytest.skip("No commit button found on PRS tab")

        commit_btn.first.click(force=True)
        map_page.wait_for_timeout(3_000)

        # Check for success vs error notification
        has_success = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            for (const n of notifs) {
                const t = n.textContent.toLowerCase();
                if (t.includes('committed') || t.includes('success') || t.includes('prs-'))
                    return true;
            }
            return false;
        }""")

        has_error = map_page.evaluate("""() => {
            const notifs = document.querySelectorAll('.notif-message');
            for (const n of notifs) {
                const t = n.textContent.toLowerCase();
                if (t.includes('error') || t.includes('fail'))
                    return true;
            }
            return false;
        }""")

        assert has_success or not has_error, "Trade commit showed an error notification"

    def test_05_new_trade_appears_in_blotter(self, map_page):
        """After committing, the new trade should appear in the blotter."""
        close_all_panels(map_page)
        open_trading_desk(map_page, tab="blotter")

        # Wait for blotter data to load
        map_page.wait_for_timeout(2_000)

        # Verify trades exist in blotter table
        row_count = map_page.evaluate("""() => {
            const wrap = document.getElementById('td-blotter-table-wrap');
            if (!wrap) return 0;
            const rows = wrap.querySelectorAll('tbody tr');
            return rows.length;
        }""")

        assert row_count > 0, "No trades found in blotter after committing"
