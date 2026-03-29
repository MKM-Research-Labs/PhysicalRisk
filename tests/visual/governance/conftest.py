# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Shared fixtures and helpers for visual.governance tests."""

import re
import subprocess
import tempfile
import os

import pytest


# ---------------------------------------------------------------------------
# Helpers (shared by js_safety_part*.py)
# ---------------------------------------------------------------------------

def js_string_newline_offenders(js: str) -> list[str]:
    """
    Return JS string literals that contain a bare newline.

    Detects the specific bug pattern where Python '\\n' (real newline char)
    ends up inside a JS single-quoted string literal, producing a
    SyntaxError in the browser.
    """
    hits = []

    # Pattern 1: string contains ONLY whitespace + newline + whitespace
    hits.extend(re.findall(r"'[ \t]*\n[ \t]*'", js))

    # Pattern 2: string opens after ( or , or =, has content, then newline
    hits.extend(re.findall(r"(?<=[\(,=])\s*'[^'\n\\]*\n[^']*'", js))

    return hits


def collect_all_governance_js() -> dict[str, str]:
    """Import every governance get_js() module and return {name: js}."""
    from visual.interactivity.governance import (
        mg_audit,
        mg_audit_reports,
        mg_bibliography,
        mg_documents,
        mg_edit_modal,
        mg_helpers,
        mg_panel_ui,
    )
    from visual.interactivity.governance.models import (
        mg_bcbs239,
        mg_chain,
        mg_detail_header,
        mg_detail_tabs,
        mg_inventory,
        mg_validation,
    )
    from visual.interactivity.governance.mrc import mg_mrc, mg_mrc_meeting
    from visual.interactivity.governance.raci import mg_raci

    modules = {
        'mg_audit':          mg_audit,
        'mg_audit_reports':  mg_audit_reports,
        'mg_bibliography':   mg_bibliography,
        'mg_documents':      mg_documents,
        'mg_edit_modal':     mg_edit_modal,
        'mg_helpers':        mg_helpers,
        'mg_panel_ui':       mg_panel_ui,
        'mg_bcbs239':        mg_bcbs239,
        'mg_chain':          mg_chain,
        'mg_detail_header':  mg_detail_header,
        'mg_detail_tabs':    mg_detail_tabs,
        'mg_inventory':      mg_inventory,
        'mg_validation':     mg_validation,
        'mg_mrc':            mg_mrc,
        'mg_mrc_meeting':    mg_mrc_meeting,
        'mg_raci':           mg_raci,
    }
    return {name: mod.get_js() for name, mod in modules.items()}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def all_governance_js():
    return collect_all_governance_js()


@pytest.fixture(scope='module')
def audit_reports_js():
    from visual.interactivity.governance import mg_audit_reports
    return mg_audit_reports.get_js()


@pytest.fixture(scope='module')
def full_governance_js():
    """Full compiled JS from ModelGovernancePanel.get_js() -- exercises the
    f-string assembly and all sub-module embedding in one shot."""
    from visual.interactivity.governance.modelgovernance import ModelGovernancePanel
    panel = ModelGovernancePanel()
    return panel.get_js()
