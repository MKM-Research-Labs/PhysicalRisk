# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Peril timeseries derivation — win / faw / fow scenario inputs.

The win (wind-only), faw (flood-AND-wind) and fow (flood-OR-wind) hazard
curves follow the same shd/she scenario protocol as the flood spine: each
mode reads a per-asset timeseries directory and the existing hazard-curve
generator prices it unchanged. This package builds those input dirs by
re-stamping the flood timeseries with the peril outcome.
"""

from port.utils.asset_config import COMMERCIAL_CONFIG, AssetTypeConfig

from .peril_ts import PerilTimeseriesGenerator


class CommercialPerilTimeseriesGenerator(PerilTimeseriesGenerator):
    """Peril ts generator for the commercial portfolio (CPROP-* assets)."""

    ASSET_CONFIG: AssetTypeConfig = COMMERCIAL_CONFIG


__all__ = ["PerilTimeseriesGenerator", "CommercialPerilTimeseriesGenerator"]
