# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Compose ``create_mapping()`` from the per-category flatten functions."""

from ..schema import DEFAULT_ELEVATION
from .contents import flatten_contents
from .hazard_profile import flatten_hazard_profile
from .header import flatten_header
from .ratings import flatten_ratings
from .resilience import flatten_resilience
from .risk_assessment import flatten_risk_assessment
from .transactions import flatten_transactions


def create_mapping(prop: dict, default_elevation: float = DEFAULT_ELEVATION) -> dict:
    """
    Flatten a nested property CDM record into a snake_case dict.

    Args:
        prop:              Nested property data in CDM format.
        default_elevation: Fallback when GroundLevelMeters is absent.

    Returns:
        Flat dict with snake_case keys.  None-valued keys are omitted.

    Raises:
        ValueError: If the mapping transformation fails unexpectedly.
    """
    try:
        flat: dict = {}
        flat.update(flatten_header(prop))
        flat.update(flatten_risk_assessment(prop, default_elevation))
        flat.update(flatten_ratings(prop))
        flat.update(flatten_hazard_profile(prop))
        flat.update(flatten_resilience(prop))
        flat.update(flatten_transactions(prop))
        flat.update(flatten_contents(prop))
        return {k: v for k, v in flat.items() if v is not None}
    except Exception as exc:
        raise ValueError(f"Error creating property mapping: {exc}") from exc
