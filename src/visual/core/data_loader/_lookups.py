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

"""Lookup-building and validation methods for the visualization data loader."""

import logging
from typing import Dict, Optional

from loaders import build_all_lookups

from ._types import DataValidationResult

logger = logging.getLogger(__name__)


class _LookupsMixin:
    """Cross-reference lookups and per-loader validation."""

    def _build_commercial_loan_lookup(self):
        """Index commercial loans by PropertyID for popup linking."""
        loans = (self.loaded_data.commercial_loan_data or {}).get('commercial_loans', [])
        lookup = {}
        for loan in loans:
            pid = loan.get('RLoan', {}).get('Header', {}).get('PropertyID')
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
