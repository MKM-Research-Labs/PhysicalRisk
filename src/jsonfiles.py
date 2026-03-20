# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Centralized JSON filename configuration for the PRS Platform.

This module provides a single source of truth for all JSON data filenames
used across the platform. This eliminates hardcoded filenames scattered
throughout the codebase.

Usage:
    from jsonfiles import JSON_FILES

    # Access specific filename
    portfolio_file = JSON_FILES['property']

    # Access with catchment-specific path
    path = config.get_input_dir() / catchment_id / JSON_FILES['gauge']
"""

from typing import Dict


class JSONFileConfig:
    """
    Configuration for all JSON data files used in the platform.

    All filenames are defined here as the single source of truth.
    When a filename needs to change, it only needs to be updated in one place.
    """

    # Portfolio data files
    PROPERTY_PORTFOLIO = 'property.json'
    GAUGE_PORTFOLIO = 'gauge.json'
    MORTGAGE_PORTFOLIO = 'mortgage.json'

    # Time series data files
    GAUGE_TIMESERIES = 'gaugets'  # Directory of per-gauge files
    STORM_TIMESERIES = 'storm_timeseries.json'
    GAUGE_FLOODTS = 'gauge_floodts.json'

    # Event data files
    STORM_EVENTS = 'storm_sequences.json'  # storm_multi sequences (replaces storms.json)
    TC_EVENTS = 'tropical_cyclone_events.json'

    # Hazard data files
    HAZARD_CURVES = 'gaugehc.json'
    PROPERTY_HAZARD_CURVES = 'propertyhc.json'
    # gauge_storm_responses merged into per-gauge files in gaugets/ directory

    # Configuration files
    CATCHMENT_CONFIG = 'catchment_config.json'
    TERRAIN_CONFIG = 'terrain_config.json'

    # Counterparty data
    COUNTERPARTY_PORTFOLIO = 'counterparty.json'

    # Swap/derivative product files
    PRS_SWAPS = 'prs_swaps.json'
    PRS_PRICING = 'prs_pricing.json'

    # Model calibration files
    HISTORICAL_GAUGES = 'historical_gauge_data.json'
    STORM_CATALOG = 'historical_storm_catalog.json'

    # Trading desk files (stored in data/output/trading/)
    MARKET_STATE = 'market_state.json'
    TRADE_MARKS = 'trade_marks.json'
    EOD_SNAPSHOTS = 'eod'  # Directory of EOD-YYYYMMDD.json files

    @classmethod
    def to_dict(cls) -> Dict[str, str]:
        """
        Return all filenames as a dictionary.

        Returns:
            Dictionary mapping descriptive keys to filenames
        """
        return {
            # Portfolio files
            'property': cls.PROPERTY_PORTFOLIO,
            'gauge': cls.GAUGE_PORTFOLIO,
            'mortgage': cls.MORTGAGE_PORTFOLIO,

            # Time series files
            'gaugets': cls.GAUGE_TIMESERIES,
            'storm_timeseries': cls.STORM_TIMESERIES,
            'gauge_floodts': cls.GAUGE_FLOODTS,

            # Event files
            'storm_events': cls.STORM_EVENTS,
            'tc_events': cls.TC_EVENTS,

            # Hazard data
            'hazard_curves': cls.HAZARD_CURVES,
            'property_hazard_curves': cls.PROPERTY_HAZARD_CURVES,
            # gauge_storm_responses merged into per-gauge files in gaugets/ directory

            # Config files
            'catchment_config': cls.CATCHMENT_CONFIG,
            'terrain_config': cls.TERRAIN_CONFIG,

            # Counterparty
            'counterparty': cls.COUNTERPARTY_PORTFOLIO,

            # Swap files
            'prs_swaps': cls.PRS_SWAPS,
            'prs_pricing': cls.PRS_PRICING,

            # Calibration files
            'historical_gauges': cls.HISTORICAL_GAUGES,
            'storm_catalog': cls.STORM_CATALOG,

            # Trading desk
            'market_state': cls.MARKET_STATE,
            'trade_marks': cls.TRADE_MARKS,
            'eod_snapshots': cls.EOD_SNAPSHOTS,
        }

    @classmethod
    def get(cls, key: str) -> str:
        """
        Get filename by key.

        Args:
            key: Descriptive key (e.g., 'property_portfolio')

        Returns:
            JSON filename

        Raises:
            KeyError: If key doesn't exist
        """
        return cls.to_dict()[key]


# Convenient singleton for easy imports
JSON_FILES = JSONFileConfig.to_dict()


# Export commonly used filenames for convenience
__all__ = [
    'JSONFileConfig',
    'JSON_FILES',
]
