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

import logging

import database

logger = logging.getLogger(__name__)


class _LoadersMixin:
    """Hazard / storm / counterparty / timeseries / optional-JSON loaders."""

    def _load_hazard_curves(self):
        """Load gauge and property hazard curves via the database seam."""
        catchment = database.active_catchment()
        # Gauge hazard curves
        try:
            hd = database.get_gauge_hazard_curves(catchment)
        except Exception as e:
            logger.error(f"Gauge hazard curves: FAILED ({e})")
            hd = None
        if hd:
            self.loaded_data.hazard_data = hd
            num_gauges = len(hd.get("hazard_curves", {}))
            meta = hd.get("metadata", {})
            dist = meta.get("distribution", "unknown")
            num_storms = meta.get("num_storms", "?")
            logger.info(f"Gauge hazard curves: {num_gauges} gauges ({dist} fit, {num_storms} storms)")
        else:
            logger.info("Gauge hazard curves: not found")

        # Property hazard curves
        try:
            phc = database.get_property_hazard_curves(catchment)
        except Exception as e:
            logger.error(f"Property hazard curves: FAILED ({e})")
            phc = None
        if phc:
            self.loaded_data.property_hazard_data = phc
            num_props = len(phc.get("property_hazard_curves", {}))
            summary = phc.get("summary", {})
            total = summary.get("total_properties", "?")
            avg_basis = summary.get("avg_basis_bps", 0)
            logger.info(f"Property hazard curves: {num_props}/{total} properties (avg basis {avg_basis:.0f}bp)")
        else:
            logger.info("Property hazard curves: not found")

    def _load_storm_data(self):
        """Load storm sequence data via the database seam."""
        try:
            storms = database.get_storm_sequences(database.active_catchment())
        except Exception as e:
            logger.error(f"Storm events: FAILED ({e})")
            storms = None
        if storms:
            self.loaded_data.storm_data = storms
            if isinstance(storms, dict):
                num_storms = len(storms.get("sequences", storms.get("storms", storms.get("items", []))))
            elif isinstance(storms, list):
                num_storms = len(storms)
            else:
                num_storms = 0
            logger.info(f"Storm events: {num_storms} storms")
        else:
            logger.info("Storm events: not found")

    def _load_counterparty_data(self):
        """Load counterparty data via the database seam."""
        try:
            ctpy = database.get_counterparty_portfolio(database.active_catchment())
        except Exception as e:
            logger.error(f"Counterparties: FAILED ({e})")
            ctpy = None
        if ctpy:
            self.loaded_data.counterparty_data = ctpy
            num = len(ctpy.get("counterparties", []))
            logger.info(f"Counterparties: {num} entities")
        else:
            logger.info("Counterparties: not found")

    def _scan_timeseries_dirs(self):
        """Report the per-asset timeseries collection sizes via the seam."""
        catchment = database.active_catchment()
        self.loaded_data.gaugets_count = sum(
            1 for _ in database.iter_gauge_timeseries_ids(catchment))
        logger.info(f"Gauge flood timeseries (gaugets): {self.loaded_data.gaugets_count} records")
        self.loaded_data.gaugehd_count = sum(
            1 for _ in database.iter_gauge_history_ids(catchment))
        logger.info(f"Gauge historical daily (gaugehd): {self.loaded_data.gaugehd_count} records")
        self.loaded_data.propertyts_count = sum(
            1 for _ in database.iter_property_timeseries_ids(catchment))
        logger.info(f"Property flood timeseries (propertyts): {self.loaded_data.propertyts_count} records")
