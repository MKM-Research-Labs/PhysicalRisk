# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial peril timeseries generator (CPROP-* assets)."""

from port.utils.asset_config import COMMERCIAL_CONFIG, AssetTypeConfig

from .peril_ts import PerilTimeseriesGenerator


class CommercialPerilTimeseriesGenerator(PerilTimeseriesGenerator):
    """Peril ts generator for the commercial portfolio (CPROP-* assets)."""

    ASSET_CONFIG: AssetTypeConfig = COMMERCIAL_CONFIG
