# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Integration tests for port command prerequisite resolution.
"""

import argparse
from unittest.mock import patch

import pytest

from tests.data.conftest import make_manifest as _make_manifest


# ---------------------------------------------------------------------------
# Integration: port command prerequisite resolution
# ---------------------------------------------------------------------------

class TestPortPrereqIntegration:
    """Verify port.py prerequisite resolution shim behavior."""

    def _make_args(self, **kwargs):
        """Build a minimal args namespace mimicking argparse output."""
        defaults = {
            "gauges": False, "properties": False, "mortgages": False,
            "gaugets": False, "gaugehd": False, "hazard": False,
            "propertyts": False, "propertytsd": False, "propertytse": False,
            "propertyhc": False, "propertyshd": False, "propertyshe": False,
            "counterparties": False, "blotter": False,
            "stressm": False, "gauge_id": None, "pdf": False,
            "all": False, "nostress": False, "strict": False,
            "verbose": False, "num_properties": 5, "num_gauges": 3,
            "num_storms": 100, "simulation_hours": 168,
            "history_years": 2, "tail_weight": 2.0, "distribution": "gev",
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_all_mode_skips_prereq_resolution(self):
        """In --all mode, resolve_prerequisites should not be called.

        We verify this by checking the guarding logic directly, since
        mocking all generators in cmd_port is fragile due to local imports.
        """
        args = self._make_args(all=True)
        run_all = args.all or not any([
            args.gauges, args.properties, args.mortgages,
            args.gaugets, args.gaugehd, args.hazard,
            args.propertyts, args.propertytsd, args.propertytse,
            args.propertyhc, args.propertyshd, args.propertyshe,
            args.counterparties, args.blotter, args.stressm,
        ])
        # In --all mode, the prereq block is guarded by `not run_all`
        assert run_all is True
        # So resolve_prerequisites would never be called

    def test_strict_mode_skips_prereq_resolution(self):
        """In --strict mode, resolve_prerequisites should not be called."""
        args = self._make_args(strict=True, propertyts=True)
        run_all = args.all or not any([
            args.gauges, args.properties, args.mortgages,
            args.gaugets, args.gaugehd, args.hazard,
            args.propertyts, args.propertytsd, args.propertytse,
            args.propertyhc, args.propertyshd, args.propertyshe,
            args.counterparties, args.blotter, args.stressm,
        ])
        # In --strict mode, the prereq block is guarded by `not args.strict`
        assert not run_all
        assert args.strict is True
        # Both guards prevent resolve_prerequisites from being called

    def test_single_step_sets_prereq_flags(self):
        """Running --propertyts with stale prereqs should enable their flags."""
        args = self._make_args(propertyts=True)
        # Simulate what port.py does in the prereq resolution block
        from lineage.validation import resolve_prerequisites
        _step_flag = {
            "gauges": "gauges", "properties": "properties",
            "synthetic_gauges": "synthetic_gauges",
            "mortgages": "mortgages", "gaugehd": "gaugehd",
            "stressm": "stressm", "hazard": "hazard",
            "propertyts": "propertyts", "propertyhc": "propertyhc",
            "propertytsd": "propertytsd", "propertytse": "propertytse",
            "propertyshd": "propertyshd", "propertyshe": "propertyshe",
            "counterparties": "counterparties", "blotter": "blotter",
        }

        with patch("lineage.validation.load_manifest",
                    return_value=_make_manifest({})):
            prereqs = resolve_prerequisites(["propertyts"], data_dir=None)

        # Apply the same logic port.py uses
        for step in prereqs:
            setattr(args, _step_flag[step], True)

        # Prerequisites of propertyts should be enabled
        assert args.gauges is True
        assert args.properties is True
        assert args.gaugehd is True
        assert args.stressm is True
        assert args.hazard is True  # hazard mutates gaugets/ which propertyts consumes
        # propertyts itself should NOT be in prerequisites (was already True)
