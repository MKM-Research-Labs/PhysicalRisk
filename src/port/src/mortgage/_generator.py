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
Mortgage Portfolio Generator.

This module generates synthetic mortgage data based on the LoanCDM schema.
Mortgages are linked to properties from the property portfolio.
Random value generation is delegated to catchment-specific modules in port.random.

Usage:
    from port.src.mortgage import MortgagePortfolioGenerator, generate_mortgages

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_mortgages()  # Uses existing property portfolio

    # Option 2: Use generator class with config defaults
    generator = MortgagePortfolioGenerator()
    result = generator.generate()

    # Option 3: Explicit module injection
    from port.random.thames import mortgage_random, params
    generator = MortgagePortfolioGenerator(
        random_module=mortgage_random,
        catchment_params=params
    )
    result = generator.generate()
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from config import config
from port.cdm import LoanCDM
from port.utils.schema import build_section

logger = logging.getLogger(__name__)


from port.utils.encoders import DateTimeEncoder  # noqa: F401

from ._generate import _MortgageGenerateMixin


class MortgagePortfolioGenerator(_MortgageGenerateMixin):
    """
    Mortgage Portfolio Generator.

    Generates synthetic mortgage data based on CDM schema.
    Mortgages are linked to properties from the property portfolio.
    Delegates random value generation to catchment-specific modules.
    """

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        """
        Initialize the Mortgage Portfolio Generator.

        Args:
            output_dir: Directory to save generated files (defaults to config.get_input_dir())
            random_module: Catchment-specific random value generator module
                          (defaults to port.random.{CATCHMENT}.mortgage_random)
            catchment_params: Catchment parameters module
                             (defaults to port.params.{CATCHMENT})
            verbose: Enable detailed processing information
        """
        # Use config defaults if not provided
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.mortgage_cdm = LoanCDM()
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        # Load catchment-specific modules from config if not provided
        self.random = random_module or config.load_random_module('mortgage.mortgage_random')
        self.params = catchment_params or config.load_params_module()

        # Processing statistics
        self.processing_stats = {
            'total_mortgages': 0,
            'successful_mortgages': 0,
            'failed_mortgages': 0,
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

def generate_mortgages(output_dir: Optional[Path] = None) -> Dict:
    """
    Convenience function to generate mortgage portfolio for current catchment.

    Uses config.CATCHMENT to determine which random module and params to use.

    Args:
        output_dir: Output directory (defaults to config.get_input_dir())
                   Must contain property.json

    Returns:
        Generation result dictionary
    """
    generator = MortgagePortfolioGenerator(output_dir=output_dir)
    return generator.generate()


if __name__ == "__main__":
    logger.info(f"Generating mortgages for catchment: {config.CATCHMENT}")
    result = generate_mortgages()
    logger.info(f"Generated {len(result['data']['mortgages'])} mortgages.")
    logger.info(f"Output saved to: {result['file_path']}")
