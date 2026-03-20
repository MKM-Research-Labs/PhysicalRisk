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
Configuration for MKM Research Labs PRS Platform.

This package exposes:
  - Config          — simple server/path config
  - PortfolioConfig — singleton used throughout app
  - config          — global PortfolioConfig singleton
  - config.models   — all analytical model parameters
"""

from config.path import ConfigPaths, PortfolioPaths
from config.server import ServerMixin
from config.catch import CatchmentMixin

# Re-export all model parameters so callers can do:
#   from config import MODEL_UNCERTAINTY_BPS
# as well as the preferred:
#   from config.models import MODEL_UNCERTAINTY_BPS
from config.port import (
    BUMP_1BP,
    DAILY_HAZARD_VOL,
    DEFAULT_YIELD_CURVE,
    GAUGE_ID_PREFIX,
    MAX_TOTAL_MOVE,
    NOTIONALS,
    NUM_BUSINESS_DAYS,
    RECOVERY,
    SEQUENCE_ID_PREFIX,
    SPATIAL_CORR_BASE_RANGE_KM,
    SPATIAL_CORR_ENABLED,
    SPATIAL_CORR_MODEL_TYPE,
    SPATIAL_CORR_NUGGET,
    SPATIAL_CORR_NUM_GAUGES,
    SPATIAL_CORR_RHO_INTENSITY,
    SPATIAL_CORR_SIGMA_LOGNORMAL,
    SPREAD_OFFSET_MAX,
    SPREAD_OFFSET_MIN,
    STORM_ID_PREFIX,
    STRESS_STORM_DEFAULT_DURATION_HOURS,
    STRESS_STORM_DEFAULT_PEAK_POSITION,
    STRESS_STORMS_MIN_COUNT,
    TENORS,
    TRIGGER_RATE_KEY,
    TRIGGERS,
)

from config.visual import (
    GAUGE_FLOOD_HIGH,
    GAUGE_FLOOD_MEDIUM,
    MAP_DEFAULT_CENTER,
    MAP_DEFAULT_TILES,
    MAP_DEFAULT_ZOOM,
    POPUP_CONTAINER_WIDTH,
    POPUP_MAX_HEIGHT_PX,
    POPUP_MAX_WIDTH,
    PROPERTY_FLOOD_HIGH,
    PROPERTY_FLOOD_MEDIUM,
)

from config.models import (
    # PRS Basis Waterfall
    MODEL_UNCERTAINTY_BPS,
    TERRAIN_BASIS_BPS,
    COMPOSITION_BASIS_BPS,
    CONSTRUCTION_YEAR_CUTOFF,
    DISTANCE_RATE_BPS_PER_KM,
    DISTANCE_MAX_BPS,
    DISTANCE_CAP_KM,
    ELEVATION_RATE_BPS_PER_M,
    ELEVATION_MAX_BENEFIT_BPS,
    RECOVERY_RATES,
    MIN_PRS_SPREAD_BPS,
    # Depth-Damage
    DEPTH_POINTS,
    DAMAGE_POINTS,
    # Velocity / Manning
    DEFAULT_ROUGHNESS,
    DEFAULT_ATTENUATION_LENGTH,
    MIN_SLOPE,
    DEFAULT_RECESSION_FACTOR,
    # Property Valuation
    BASE_AREA_RANGES,
    BASE_PRICE_PER_SQM,
    AGE_BAND_FACTORS,
    CONDITION_FACTORS,
    FLOOD_RISK_FACTORS,
    EPC_FACTORS,
    PROXIMITY_ZONES,
    RENTAL_YIELD_RATES,
    RENT_PER_SQM,
    MIN_PROPERTY_VALUE,
    MAX_PROPERTY_VALUE,
    # Insurance Premium
    PROPERTY_TYPE_PREMIUM_FACTORS,
    FLOOD_RISK_PREMIUM_FACTORS,
    AGE_PREMIUM_FACTORS,
    CONSTRUCTION_TYPE_FACTORS,
    AREA_PREMIUM_BANDS,
    BASE_RATE_RANGE,
    MIN_PREMIUM,
    MAX_PREMIUM,
)

class Config(ConfigPaths, ServerMixin):
    """Lightweight application configuration (server + paths)."""


# Singleton instance
config = Config()


class PortfolioConfig(PortfolioPaths, ServerMixin, CatchmentMixin):
    """
    Configuration manager for portfolio generation.

    Implements singleton pattern to ensure consistent configuration
    across all modules.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Catchment state (defined in CatchmentMixin) — must come first
        # so _init_paths can use self._catchment_id
        self._init_catchment()

        # Path attributes (defined in PortfolioPaths)
        self._init_paths(self._catchment_id)

        # Add all dirs to sys.path
        self._setup_paths()

        self._initialized = True

    def __repr__(self) -> str:
        return (
            f"PortfolioConfig("
            f"catchment='{self._catchment_id}', "
            f"root='{self.project_root}')"
        )


# Global singleton instance
config = PortfolioConfig()
