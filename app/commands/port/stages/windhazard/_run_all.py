# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Ordered driver that runs every wind-coupled peril sub-stage in sequence."""

from ...context import StageContext
from .property import (
    run_property_peril_ts,
    run_propertywin, run_propertyfaw, run_propertyfow,
    run_propertybow, run_propertybaw, run_property_peril_decomposition,
    run_property_peril_placeholders,
)
from .commercial import (
    run_commercial_peril_ts,
    run_commercialwin, run_commercialfaw, run_commercialfow,
    run_commercialbow, run_commercialbaw, run_commercial_peril_decomposition,
    run_commercial_peril_placeholders,
)


def run_all(ctx: StageContext):
    run_property_peril_ts(ctx)
    run_propertywin(ctx)
    run_propertyfaw(ctx)
    run_propertyfow(ctx)
    run_propertybow(ctx)
    run_propertybaw(ctx)
    # Write zero-event placeholders BEFORE decomposition so the canonical
    # peril fan is rebuilt from fresh no-wind files (and any stale wind files
    # from a prior typhoon run are overwritten first).
    run_property_peril_placeholders(ctx)
    run_property_peril_decomposition(ctx)
    run_commercial_peril_ts(ctx)
    run_commercialwin(ctx)
    run_commercialfaw(ctx)
    run_commercialfow(ctx)
    run_commercialbow(ctx)
    run_commercialbaw(ctx)
    run_commercial_peril_placeholders(ctx)
    run_commercial_peril_decomposition(ctx)
