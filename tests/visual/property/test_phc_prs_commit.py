# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

"""Tests for PRS commit payload — ensures gauge_id and gauge_name are sent.

Regression test: the property PRS commit was missing gauge_id in the payload,
causing 'gauge_id is required' errors from the backend.
"""

import pytest

from visual.interactivity.property import phc_prs


@pytest.fixture(scope='module')
def prs_js():
    """Get PRS commit JS once for all tests."""
    return phc_prs.get_js()


class TestPRSCommitPayload:
    """Commit payload must include all fields required by /api/v1/prs/commit."""

    def test_payload_has_gauge_id(self, prs_js):
        """gauge_id must be in the commit payload."""
        idx = prs_js.index('var payload = {')
        snippet = prs_js[idx:idx + 800]
        assert 'gauge_id:' in snippet, (
            "Commit payload missing gauge_id — backend will reject with "
            "'gauge_id is required'"
        )

    def test_payload_has_gauge_name(self, prs_js):
        """gauge_name must be in the commit payload."""
        idx = prs_js.index('var payload = {')
        snippet = prs_js[idx:idx + 800]
        assert 'gauge_name:' in snippet, (
            "Commit payload missing gauge_name — CDM record GaugeName will be empty"
        )

    def test_gauge_id_from_gauge_components(self, prs_js):
        """gauge_id should be extracted from gaugeComponents (nearest gauge)."""
        assert 'primaryGauge' in prs_js
        assert 'primaryGauge.gauge_id' in prs_js

    def test_payload_has_property_id(self, prs_js):
        """property_id must be in the commit payload."""
        idx = prs_js.index('var payload = {')
        snippet = prs_js[idx:idx + 800]
        assert 'property_id:' in snippet

    def test_payload_has_counterparty(self, prs_js):
        """counterparty_id must be in the commit payload."""
        idx = prs_js.index('var payload = {')
        snippet = prs_js[idx:idx + 800]
        assert 'counterparty_id:' in snippet

    def test_payload_has_gauge_components(self, prs_js):
        """gauge_components array must be in the commit payload."""
        idx = prs_js.index('var payload = {')
        snippet = prs_js[idx:idx + 1200]
        assert 'gauge_components:' in snippet

    def test_commit_posts_to_prs_endpoint(self, prs_js):
        """Commit must POST to /api/v1/prs/commit."""
        assert '/api/v1/prs/commit' in prs_js

    def test_commit_function_exists(self, prs_js):
        """commitPropertyPRSTrade must be exposed on window."""
        assert 'commitPropertyPRSTrade' in prs_js


class TestPRSCommitResponseHandling:
    """Commit response handling — success notification, PDF display, blotter refresh."""

    def test_success_shows_swap_id(self, prs_js):
        """Success notification should include the new swap_id."""
        assert 'data.swap_id' in prs_js
        assert 'showSuccess' in prs_js

    def test_success_refreshes_active_gauges(self, prs_js):
        """After commit, active gauges list must be refreshed."""
        assert '/api/v1/trading/blotter/active-gauges' in prs_js

    def test_error_restores_button(self, prs_js):
        """On error, commit button must be re-enabled."""
        assert "btn.disabled = false" in prs_js
