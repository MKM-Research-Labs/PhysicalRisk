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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Flood Gauge Portfolio Generator.

This module generates synthetic flood gauge data based on the FloodGaugeCDM schema.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.gauge import GaugePortfolioGenerator, generate_gauges

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_gauges(count=40)

    # Option 2: Use generator class with config defaults
    generator = GaugePortfolioGenerator()
    result = generator.generate(count=40)

    # Option 3: Explicit module injection
    from port.random.thames import gauge_random, params
    generator = GaugePortfolioGenerator(
        random_module=gauge_random,
        catchment_params=params
    )
    result = generator.generate(count=40)
"""

import logging
from typing import Any, Dict, Optional

import database
from config import config
from port.cdm import FloodGaugeCDM

logger = logging.getLogger(__name__)

from port.utils.encoders import DateTimeEncoder  # noqa: F401

from ._gauge_generate import _GaugeGenerateMixin


class GaugePortfolioGenerator(_GaugeGenerateMixin):
    """
    Flood Gauge Portfolio Generator.

    Generates synthetic flood gauge data based on CDM schema.
    Delegates random value generation to catchment-specific modules.
    """

    def __init__(
        self,
        catchment: Optional[str] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        """
        Initialize the Flood Gauge Portfolio Generator.

        Args:
            catchment: Catchment to generate for; storage is resolved inside the
                       ``database`` package (defaults to ``database.active_catchment()``)
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.gauge_random)
            catchment_params: Catchment parameters module
                             (defaults to port.random.{CATCHMENT}.params)
            verbose: Enable detailed processing information
        """
        # Run-scoped catchment identity; storage location lives in ``database``.
        self.catchment = catchment or database.active_catchment()

        self.flood_gauge_cdm = FloodGaugeCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        # Load catchment-specific modules from config if not provided
        self.random = random_module or config.load_random_module('gauge.gauge_random')
        self.params = catchment_params or config.load_params_module()

        # Get catchment name for gauge naming
        self.catchment_name = getattr(self.params, 'DISPLAYNAME',
                                      getattr(self.params, 'NAME',
                                             config.CATCHMENT.capitalize()))

        # Processing statistics
        self.processing_stats = {
            'total_gauges': 0,
            'successful_gauges': 0,
            'failed_gauges': 0,
            'elevation_successes': 0,
            'elevation_failures': 0,
            'start_time': None,
            'end_time': None
        }

    def log(self, message: str, level: str = "INFO"):
        """Log processing information."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_gauges(count: int = 40, catchment: Optional[str] = None) -> Dict:
    """
    Convenience function to generate flood gauge portfolio for current catchment.

    Uses config.CATCHMENT to determine which random module and params to use.

    Args:
        count: Number of gauges to generate
        catchment: Catchment to generate for (defaults to ``database.active_catchment()``)

    Returns:
        Generation result dictionary
    """
    generator = GaugePortfolioGenerator(catchment=catchment)
    return generator.generate(count=count)


if __name__ == "__main__":
    logger.info(f"Generating gauges for catchment: {config.CATCHMENT}")
    result = generate_gauges(count=40)
    logger.info(f"Generated {len(result['data']['flood_gauges'])} gauges.")
    logger.info(f"Saved to catchment: {result['catchment']}")
