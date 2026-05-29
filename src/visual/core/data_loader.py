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

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

from config import config
from jsonfiles import JSONFileConfig
from loaders import (
    GaugeLoader,
    RLoanLoader,
    PropertyLoader,
    build_all_lookups,
)

from . import _data_summary

logger = logging.getLogger(__name__)


@dataclass
class LoadedData:
    """Container for all loaded visualization data."""
    gauge_data: Optional[Dict[str, Any]] = None
    property_data: Optional[Dict[str, Any]] = None
    rloan_data: Optional[Dict[str, Any]] = None
    commercial_data: Optional[Dict[str, Any]] = None
    commercial_loan_data: Optional[Dict[str, Any]] = None
    hazard_data: Optional[Dict[str, Any]] = None
    property_hazard_data: Optional[Dict[str, Any]] = None
    storm_data: Optional[Dict[str, Any]] = None
    counterparty_data: Optional[Dict[str, Any]] = None

    # Directory-based data counts
    gaugets_count: int = 0
    gaugehd_count: int = 0
    propertyts_count: int = 0

    # Processed lookups
    rloan_lookup: Optional[Dict[str, Dict]] = None
    commercial_loan_lookup: Optional[Dict[str, Dict]] = None
    gauge_flood_info: Optional[Dict[str, Dict]] = None
    property_flood_info: Optional[Dict[str, Dict]] = None


class DataValidationResult(NamedTuple):
    """Result of data validation."""
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    summary: Dict[str, Any]


class DataLoader:
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
        self._rloan_loader = RLoanLoader(self.input_dir, filename=JSONFileConfig.MORTGAGE_PORTFOLIO)

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
        # without commercial.json) ---
        self.loaded_data.commercial_data = self._load_optional_json(
            self.input_dir / JSONFileConfig.COMMERCIAL_PORTFOLIO,
            "commercial",
        )
        self.loaded_data.commercial_loan_data = self._load_optional_json(
            self.input_dir / JSONFileConfig.COMMERCIAL_LOAN_PORTFOLIO,
            "commercial_loan",
        )

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

    def _load_hazard_curves(self):
        """Load gauge and property hazard curve files."""
        # Gauge hazard curves
        hc_path = self.input_dir / JSONFileConfig.HAZARD_CURVES
        if hc_path.exists():
            try:
                with open(hc_path, 'r') as f:
                    self.loaded_data.hazard_data = json.load(f)
                num_gauges = len(self.loaded_data.hazard_data.get("hazard_curves", {}))
                meta = self.loaded_data.hazard_data.get("metadata", {})
                dist = meta.get("distribution", "unknown")
                num_storms = meta.get("num_storms", "?")
                logger.info(f"Gauge hazard curves: {num_gauges} gauges ({dist} fit, {num_storms} storms)")
            except Exception as e:
                logger.error(f"Gauge hazard curves: FAILED ({e})")
        else:
            logger.info(f"Gauge hazard curves: not found ({JSONFileConfig.HAZARD_CURVES})")

        # Property hazard curves
        phc_path = self.input_dir / JSONFileConfig.PROPERTY_HAZARD_CURVES
        if phc_path.exists():
            try:
                with open(phc_path, 'r') as f:
                    self.loaded_data.property_hazard_data = json.load(f)
                phc = self.loaded_data.property_hazard_data
                num_props = len(phc.get("property_hazard_curves", {}))
                summary = phc.get("summary", {})
                total = summary.get("total_properties", "?")
                avg_basis = summary.get("avg_basis_bps", 0)
                logger.info(f"Property hazard curves: {num_props}/{total} properties (avg basis {avg_basis:.0f}bp)")
            except Exception as e:
                logger.error(f"Property hazard curves: FAILED ({e})")
        else:
            logger.info(f"Property hazard curves: not found ({JSONFileConfig.PROPERTY_HAZARD_CURVES})")

    def _load_storm_data(self):
        """Load storm event data."""
        storm_path = self.input_dir / JSONFileConfig.STORM_EVENTS
        if storm_path.exists():
            try:
                with open(storm_path, 'r') as f:
                    self.loaded_data.storm_data = json.load(f)
                storms = self.loaded_data.storm_data
                if isinstance(storms, dict):
                    num_storms = len(storms.get("sequences", storms.get("storms", storms.get("items", []))))
                elif isinstance(storms, list):
                    num_storms = len(storms)
                else:
                    num_storms = 0
                size_kb = storm_path.stat().st_size / 1024
                logger.info(f"Storm events: {num_storms} storms ({size_kb:.0f} KB)")
            except Exception as e:
                logger.error(f"Storm events: FAILED ({e})")
        else:
            logger.info(f"Storm events: not found ({JSONFileConfig.STORM_EVENTS})")

    def _load_counterparty_data(self):
        """Load counterparty data."""
        ctpy_path = self.input_dir / JSONFileConfig.COUNTERPARTY_PORTFOLIO
        if ctpy_path.exists():
            try:
                with open(ctpy_path, 'r') as f:
                    self.loaded_data.counterparty_data = json.load(f)
                num = len(self.loaded_data.counterparty_data.get("counterparties", []))
                logger.info(f"Counterparties: {num} entities")
            except Exception as e:
                logger.error(f"Counterparties: FAILED ({e})")
        else:
            logger.info(f"Counterparties: not found ({JSONFileConfig.COUNTERPARTY_PORTFOLIO})")

    def _scan_timeseries_dirs(self):
        """Scan time series directories and report counts."""
        # Gauge timeseries (gaugets/)
        gaugets_dir = self.input_dir / JSONFileConfig.GAUGE_TIMESERIES
        if gaugets_dir.exists() and gaugets_dir.is_dir():
            files = list(gaugets_dir.glob("*.json"))
            self.loaded_data.gaugets_count = len(files)
            logger.info(f"Gauge flood timeseries (gaugets/): {len(files)} gauge files")
        else:
            logger.info("Gauge flood timeseries (gaugets/): not found")

        # Gauge historical daily (gaugehd/)
        gaugehd_dir = self.input_dir / "gaugehd"
        if gaugehd_dir.exists() and gaugehd_dir.is_dir():
            files = list(gaugehd_dir.glob("*.json"))
            self.loaded_data.gaugehd_count = len(files)
            logger.info(f"Gauge historical daily (gaugehd/): {len(files)} gauge files")
        else:
            logger.info("Gauge historical daily (gaugehd/): not found")

        # Property timeseries (propertyts/)
        propertyts_dir = self.input_dir / "propertyts"
        if propertyts_dir.exists() and propertyts_dir.is_dir():
            files = list(propertyts_dir.glob("*.json"))
            self.loaded_data.propertyts_count = len(files)
            has_summary = (propertyts_dir / "portfolio_summary.json").exists()
            summary_note = " (incl. portfolio summary)" if has_summary else ""
            logger.info(f"Property flood timeseries (propertyts/): {len(files)} files{summary_note}")
        else:
            logger.info("Property flood timeseries (propertyts/): not found")

    def _load_optional_json(self, path: Path, data_type: str) -> Optional[Dict]:
        """Load a JSON file if it exists; silently return None if not.

        Used for portfolios that may be absent (commercial.json,
        commercial_loan.json) — their layers degrade gracefully when
        the catchment has no commercial portfolio.
        """
        if not path.exists():
            logger.debug(f"{data_type} portfolio not found at {path} — skipping")
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            n = (len(data.get('commercial_assets', []))
                 or len(data.get('commercial_loans', []))
                 or len(data) if isinstance(data, dict) else 0)
            logger.info(f"Loaded {n} {data_type} records from {path.name}")
            return data
        except Exception as e:
            logger.error(f"Error loading {data_type} from {path}: {e}")
            return None

    def _build_commercial_loan_lookup(self):
        """Index commercial loans by PropertyID for popup linking."""
        loans = (self.loaded_data.commercial_loan_data or {}).get('commercial_loans', [])
        lookup = {}
        for loan in loans:
            pid = loan.get('Mortgage', {}).get('Header', {}).get('PropertyID')
            if pid:
                lookup[pid] = loan
        self.loaded_data.commercial_loan_lookup = lookup

    def _load_with_validation(self, loader, data_type: str) -> Optional[Dict]:
        """Load data using a loader and record validation result."""
        try:
            data_list = loader.load_all()

            if data_list:
                data = {"items": data_list, "count": len(data_list)}

                self._validation_results[data_type] = DataValidationResult(
                    is_valid=True,
                    warnings=[],
                    errors=[],
                    summary={"type": data_type, "loaded": True, "count": len(data_list)}
                )

                logger.info(f"Loaded {len(data_list)} {data_type} records")
                return data
            else:
                logger.warning(f"No data loaded for {data_type}")
                self._validation_results[data_type] = DataValidationResult(
                    is_valid=False,
                    warnings=[],
                    errors=["No data loaded"],
                    summary={"type": data_type, "loaded": False}
                )
                return None

        except Exception as e:
            logger.error(f"Error loading {data_type}: {e}", exc_info=True)
            self._validation_results[data_type] = DataValidationResult(
                is_valid=False,
                warnings=[],
                errors=[str(e)],
                summary={"type": data_type, "error": str(e)}
            )
            return None

    def _build_lookups(self):
        """Build cross-reference lookup tables."""
        logger.info("Building lookup tables...")

        lookups = build_all_lookups(
            gauge_data=self.loaded_data.gauge_data,
            property_data=self.loaded_data.property_data,
            rloan_data=self.loaded_data.rloan_data,
            flood_risk_data=self.loaded_data.hazard_data,
            property_hazard_data=self.loaded_data.property_hazard_data
        )

        self.loaded_data.rloan_lookup = lookups["rloan_lookup"]
        self.loaded_data.gauge_flood_info = lookups["gauge_flood_info"]
        self.loaded_data.property_flood_info = lookups["property_flood_info"]
        self._build_commercial_loan_lookup()

        logger.info(f"Mortgage lookup: {len(self.loaded_data.rloan_lookup)} entries")
        logger.info(f"Gauge flood info: {len(self.loaded_data.gauge_flood_info)} entries")
        logger.info(f"Property flood info: {len(self.loaded_data.property_flood_info)} entries")
        if self.loaded_data.commercial_loan_lookup:
            logger.info(f"Commercial loan lookup: {len(self.loaded_data.commercial_loan_lookup)} entries")

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
