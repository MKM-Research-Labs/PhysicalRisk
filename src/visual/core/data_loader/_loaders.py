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

"""File/directory loading methods for the visualization data loader."""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from jsonfiles import JSONFileConfig

logger = logging.getLogger(__name__)


class _LoadersMixin:
    """Hazard / storm / counterparty / timeseries / optional-JSON loaders."""

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
