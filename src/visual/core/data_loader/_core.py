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
Data loading coordinator for the visualization system.

Thin wrapper around the loaders package for visualization-specific needs.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import database
from config import config
from jsonfiles import JSONFileConfig
from loaders import GaugeLoader, PropertyLoader, RLoanLoader

from .. import _data_summary
from ._loaders import _LoadersMixin
from ._lookups import _LookupsMixin
from ._types import DataValidationResult, LoadedData

logger = logging.getLogger(__name__)

__all__ = ["DataLoader", "LoadedData", "DataValidationResult"]


class DataLoader(_LoadersMixin, _LookupsMixin):
    """
    Coordinates data loading for visualization using the loaders package.

    This is a thin wrapper that delegates to the modular loaders
    and builds cross-reference lookups for visualization.
    """

    def __init__(self, input_dir: Optional[Path] = None):
        """Initialize the data loader."""
        self.input_dir = Path(input_dir) if input_dir else config.get_input_dir()
        self.loaded_data = LoadedData()
        self._validation_results: Dict[str, DataValidationResult] = {}

        # Initialize loaders with input directory
        self._gauge_loader = GaugeLoader(self.input_dir, filename=JSONFileConfig.GAUGE_PORTFOLIO)
        self._property_loader = PropertyLoader(self.input_dir, filename=JSONFileConfig.PROPERTY_PORTFOLIO)
        self._rloan_loader = RLoanLoader(self.input_dir, filename=JSONFileConfig.RLOAN_PORTFOLIO)

        logger.info(f"DataLoader initialized with input directory: {self.input_dir}")

    def load_all_data(self) -> LoadedData:
        """
        Load all required data files using JSONFileConfig and build lookup tables.

        Returns:
            LoadedData container with all loaded and processed data
        """
        logger.info(f"DATA LOADING - {config.catchment_id}")
        logger.info(f"Source: {self.input_dir}")

        # --- Portfolio data (core) ---
        logger.info("Loading portfolio data...")
        self.loaded_data.gauge_data = self._load_with_validation(
            self._gauge_loader, "gauge"
        )
        self.loaded_data.property_data = self._load_with_validation(
            self._property_loader, "property"
        )
        self.loaded_data.rloan_data = self._load_with_validation(
            self._rloan_loader, "mortgage"
        )

        # --- Commercial portfolio (optional — silently absent for catchments
        # without a commercial portfolio) ---
        _catchment = database.active_catchment()
        self.loaded_data.commercial_data = database.get_commercial_portfolio(_catchment)
        self.loaded_data.commercial_loan_data = database.get_commercial_loan_portfolio(_catchment)

        # --- Hazard curves ---
        logger.info("Loading hazard curves...")
        self._load_hazard_curves()

        # --- Storm data ---
        logger.info("Loading storm & event data...")
        self._load_storm_data()

        # --- Counterparty data ---
        self._load_counterparty_data()

        # --- Time series directories ---
        logger.info("Scanning time series data...")
        self._scan_timeseries_dirs()

        # --- Build lookups ---
        self._build_lookups()

        # --- Relationships & summary ---
        self._print_relationship_analysis()
        self._print_loading_summary()

        return self.loaded_data

    def _print_relationship_analysis(self):
        """Print ID relationship analysis for debugging."""
        _data_summary.print_relationship_analysis(self)

    def _print_loading_summary(self):
        """Print a comprehensive summary of all loaded data."""
        _data_summary.print_loading_summary(self)

    def is_data_complete(self) -> bool:
        """Check if minimum required data (gauge data) is loaded."""
        return self.loaded_data.gauge_data is not None

    def get_validation_summary(self) -> Dict[str, DataValidationResult]:
        """Get validation results for all loaded data."""
        return self._validation_results.copy()

    def get_data_summary(self) -> Dict[str, Any]:
        """Get a summary of all loaded data."""
        return _data_summary.build_data_summary(self)
