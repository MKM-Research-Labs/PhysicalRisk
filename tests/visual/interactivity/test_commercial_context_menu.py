# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial context-menu wiring tests.

Covers the Python side: DEFAULT_COMMERCIAL_MENU shape, ContextMenuHandler
accepts and exposes a commercial menu, and the embedded JS config carries
the 'commercial' key with the new vocabulary (Commercial / Loan labels).
"""

import json
import re

import pytest

from visual.interactivity.context_menus import (
    DEFAULT_COMMERCIAL_MENU,
    DEFAULT_PROPERTY_MENU,
    ContextMenuHandler,
)


class TestDefaultCommercialMenu:

    def test_has_eight_items(self):
        assert len(DEFAULT_COMMERCIAL_MENU) == 8

    def test_labels_use_commercial_and_loan_vocabulary(self):
        labels = [item["label"] for item in DEFAULT_COMMERCIAL_MENU]
        joined = " | ".join(labels)
        assert "Commercial Details" in joined
        assert "Loan Details" in joined
        assert "Generate Commercial Report" in joined
        assert "Generate Loan Report" in joined
        # No residential vocab.
        assert "Property Details" not in joined
        assert "Mortgage Details" not in joined
        assert "Generate Property Report" not in joined
        assert "Generate Mortgage Report" not in joined

    def test_storms_and_swap_present(self):
        actions = [item["action"] for item in DEFAULT_COMMERCIAL_MENU]
        assert "viewCommercialStorms" in actions
        assert "viewCommercialHazard" in actions

    def test_unique_action_handlers(self):
        actions = [item["action"] for item in DEFAULT_COMMERCIAL_MENU]
        assert len(set(actions)) == len(actions)

    def test_actions_distinct_from_property_menu(self):
        prop_actions = {item["action"] for item in DEFAULT_PROPERTY_MENU}
        com_actions = {item["action"] for item in DEFAULT_COMMERCIAL_MENU}
        # Commercial actions must NOT alias property actions — they need
        # their own backend handlers (storm scenarios + swap will be
        # plumbed in shortly).
        assert prop_actions.isdisjoint(com_actions)


class TestContextMenuHandlerCommercial:

    def test_default_handler_has_commercial_menu(self):
        h = ContextMenuHandler()
        assert h.commercial_menu == DEFAULT_COMMERCIAL_MENU
        assert h.commercial_menu is not DEFAULT_COMMERCIAL_MENU  # copy

    def test_custom_commercial_menu_accepted(self):
        custom = [{"id": "x", "label": "Custom", "action": "doX"}]
        h = ContextMenuHandler(commercial_menu=custom)
        assert h.commercial_menu == custom

    def test_configure_updates_commercial_menu(self):
        h = ContextMenuHandler()
        custom = [{"id": "y", "label": "Custom Y", "action": "doY"}]
        h.configure(commercial_menu=custom)
        assert h.commercial_menu == custom

    def test_emitted_menu_config_includes_commercial_key(self):
        h = ContextMenuHandler()
        js = h.get_js()
        # Extract the __MENU_CONFIG JSON object embedded in the JS.
        m = re.search(r"window\.__MENU_CONFIG\s*=\s*(\{.*?\});", js, re.DOTALL)
        assert m, "MENU_CONFIG not embedded"
        cfg = json.loads(m.group(1))
        assert "commercial" in cfg
        assert isinstance(cfg["commercial"], list)
        assert len(cfg["commercial"]) == len(DEFAULT_COMMERCIAL_MENU)
        # Spot-check label round-trips through JSON.
        labels = [item["label"] for item in cfg["commercial"]]
        assert any("Commercial Details" in l for l in labels)
        assert any("Loan Details" in l for l in labels)
