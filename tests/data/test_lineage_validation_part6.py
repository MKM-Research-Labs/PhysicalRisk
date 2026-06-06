# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Unit tests for lineage validation — completeness, full chain (part 6).
"""

from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


# ===========================================================================
# Coverage: STEP_OWNERS — lock in the typhoon + commercial additions
# ===========================================================================

class TestHelpersResidualBranches:
    """Mop-up tests for the last uncovered lines in _helpers.py."""

    def test_current_hash_returns_missing_for_non_dict_entry(self):
        """_current_hash: outputs entry is a string (legacy/corrupt) → _MISSING."""
        from lineage.validation._helpers import _current_hash, _MISSING
        step = {"outputs": {"gauge.json": "not a dict"}}
        assert _current_hash("gauge.json", step) is _MISSING

    def test_live_hash_resolves_data_dir_when_none(self, tmp_path, monkeypatch):
        """_live_hash with data_dir=None calls _resolve_data_dir internally."""
        from lineage.validation import _helpers
        # Point the resolver at an empty tmp dir so the call returns None
        # (artifact missing) rather than hashing real catchment data.
        monkeypatch.setattr(_helpers, "_resolve_data_dir", lambda: tmp_path)
        result = _helpers._live_hash("does_not_exist.json")
        assert result is None


class TestStepOwnersNewEntries:
    """Lock in the recently-added STEP_OWNERS entries for typhoon and the
    commercial chain — regression guard so these aren't dropped silently."""

    def test_typhoon_owner_set(self):
        from docs.models.data_lineage import STEP_OWNERS
        assert STEP_OWNERS.get("typhoon") == "Quantitative Analytics"

    def test_commercial_chain_owners_set(self):
        from docs.models.data_lineage import STEP_OWNERS
        # commercial is a data-source step; the time-series derivatives are
        # quant-owned (parallel to property* / propertyts* etc.).
        assert STEP_OWNERS.get("commercial") == "Data Engineering"
        for step in (
            "commercialts", "commercialtsd", "commercialtse",
            "commercialhc", "commercialshd", "commercialshe",
        ):
            assert STEP_OWNERS.get(step) == "Quantitative Analytics", (
                f"STEP_OWNERS missing or wrong for '{step}'"
            )
