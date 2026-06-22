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


"""Counterparty portfolio generator (orchestration)."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import database
from config import config
from port.cdm.ctpy import CounterpartyCDM

from port.src.counterparty._data import _ALL_COUNTERPARTIES
from port.src.counterparty._records import _RecordBuilderMixin

logger = logging.getLogger(__name__)


class CounterpartyPortfolioGenerator(_RecordBuilderMixin):
    """Generates a portfolio of synthetic counterparties for PRS trading."""

    def __init__(self, catchment: Optional[str] = None, verbose: bool = True):
        # Run-scoped catchment identity; storage location lives in ``database``.
        self.catchment = catchment or database.active_catchment()
        self.cdm = CounterpartyCDM()
        self.verbose = verbose

    def generate(self, count: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate counterparty portfolio.

        Args:
            count: Number of counterparties (defaults to all predefined names)

        Returns:
            Dict with 'data', 'catchment', and 'metadata'
        """
        if count is None:
            names = _ALL_COUNTERPARTIES
        else:
            names = _ALL_COUNTERPARTIES[:count]

        # Always emit the fixed REIT counterparty first.  Property PRS
        # trades are exclusively between the trader and CTPY-REIT-001
        # (see book_property.py); the lineage / blotter tests assert
        # that every PRS counterparty exists in counterparty.json, so
        # this entry must always be present.
        counterparties = [self._generate_reit()]
        if self.verbose:
            logger.info(
                "[REIT] Thames Property REIT (CTPY-REIT-001)"
            )

        for i, (full_name, short_name, ctpy_type) in enumerate(names):
            ctpy = self._generate_one(i, full_name, short_name, ctpy_type)
            counterparties.append(ctpy)
            if self.verbose:
                party_id = ctpy["CounterpartySet"]["Party"]["PartyID"]
                logger.info("[%d/%d] %s (%s)", i+1, len(names), short_name, party_id)

        output_data = {
            "counterparties": counterparties,
            "generation_metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "v1.0",
                "catchment": config.catchment_id,
                "total_generated": len(counterparties),
            }
        }

        # Persist through the database seam (catchment-keyed, storage-agnostic).
        database.save_counterparties(self.catchment, output_data)

        if self.verbose:
            logger.info("Wrote %d counterparties for catchment %s",
                        len(counterparties), self.catchment)

        return {
            "data": counterparties,
            "catchment": self.catchment,
            "metadata": output_data["generation_metadata"],
        }


def generate_counterparties(catchment=None, count=None, verbose=True):
    """Convenience function."""
    gen = CounterpartyPortfolioGenerator(catchment=catchment, verbose=verbose)
    return gen.generate(count)
