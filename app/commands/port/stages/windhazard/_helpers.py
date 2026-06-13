# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Shared predicates for the wind-coupled hazard stages."""

from ...context import StageContext


def _damage_available(ctx: StageContext) -> bool:
    """True when the typhoon damage join input exists for this catchment."""
    damage_dir = ctx.input_dir / "typhoon" / "damage"
    return damage_dir.exists() and any(damage_dir.glob("EVT-*.json"))


def _peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "propertytsw", "propertytsfaw", "propertytsfow",
        "propertytsbow", "propertytsbaw",
        "propertywin", "propertyfaw", "propertyfow",
        "propertybow", "propertybaw",
    ))


def _commercial_peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "commercialtsw", "commercialtsfaw", "commercialtsfow",
        "commercialtsbow", "commercialtsbaw",
        "commercialwin", "commercialfaw", "commercialfow",
        "commercialbow", "commercialbaw",
    ))
