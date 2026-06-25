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
Mortgage data loader for MKM Research Labs PRS Platform.

Handles loading and querying mortgage portfolio data.
"""

import logging
from typing import Any, Dict, List, Optional

from .base_loader import BaseLoader

logger = logging.getLogger(__name__)


class RLoanLoader(BaseLoader[Dict[str, Any]]):
    """
    Loader for mortgage portfolio data.

    Handles the loan.json file with structure:
    {
        "mortgages": [
            {
                "RLoanID": "...",
                "PropertyID": "...",
                "LoanAmount": ...,
                ...
            }
        ]
    }
    """

    ENTITY_NAME = 'rloan'
    DEFAULT_FILENAME = 'loan.json'
    CONTAINER_KEYS = ['loans', 'portfolio', 'mortgages']

    # NOTE: not yet migrated to the seam. The real loan shape is nested
    # ({RLoan:{Header:{RLoanID}}}, which is what the pg `loan` collection keys on),
    # but this loader's get_entity_id/get_entity_summary read a FLAT RLoanID — a
    # pre-existing inconsistency. Migrating to get_loan_portfolio needs that resolved
    # (+ the conftest's flat mortgage_json), so it's a separate batch.

    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract RLoanID from entity."""
        return entity.get('RLoanID')

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create mortgage summary for listing."""
        return {
            'mortgageId': entity.get('RLoanID'),
            'propertyId': entity.get('PropertyID'),
            'loanAmount': entity.get('LoanAmount'),
            'interestRate': entity.get('InterestRate'),
            'loanType': entity.get('LoanType'),
            'lender': entity.get('Lender'),
            'status': entity.get('Status'),
        }

    # =========================================================================
    # Mortgage-specific query methods
    # =========================================================================

    def find_by_property_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """
        Find mortgage linked to a property.

        This is the primary lookup method used when generating property reports
        that include mortgage information.

        Args:
            property_id: The PropertyID to search for

        Returns:
            Mortgage dictionary or None if not found
        """
        for entity in self.load_all():
            # Check top-level and nested Mortgage.Header.PropertyID
            prop_id = entity.get('PropertyID')
            if not prop_id:
                prop_id = entity.get('RLoan', {}).get('Header', {}).get('PropertyID')
            if prop_id == property_id:
                logger.debug(f"Found mortgage for property: {property_id}")
                return entity

        logger.debug(f"No mortgage found for property: {property_id}")
        return None

    def find_by_lender(self, lender: str) -> List[Dict[str, Any]]:
        """
        Find all mortgages from a specific lender.

        Args:
            lender: Lender name to filter by

        Returns:
            List of matching mortgages
        """
        lender_lower = lender.lower()
        results = []
        for entity in self.load_all():
            entity_lender = entity.get('Lender', '')
            if lender_lower in entity_lender.lower():
                results.append(entity)
        return results

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Find all mortgages with a specific status.

        Args:
            status: Status to filter by (e.g., 'Active', 'Delinquent')

        Returns:
            List of matching mortgages
        """
        status_lower = status.lower()
        results = []
        for entity in self.load_all():
            entity_status = entity.get('Status', '')
            if entity_status.lower() == status_lower:
                results.append(entity)
        return results

    def get_total_exposure(self) -> float:
        """
        Calculate total loan exposure across all mortgages.

        Returns:
            Sum of all LoanAmount values
        """
        total = 0.0
        for entity in self.load_all():
            amount = entity.get('LoanAmount', 0)
            if isinstance(amount, (int, float)):
                total += amount
        return total

    def get_exposure_by_lender(self) -> Dict[str, float]:
        """
        Calculate loan exposure grouped by lender.

        Returns:
            Dictionary mapping lender names to total exposure
        """
        exposure = {}
        for entity in self.load_all():
            lender = entity.get('Lender', 'Unknown')
            amount = entity.get('LoanAmount', 0)
            if isinstance(amount, (int, float)):
                exposure[lender] = exposure.get(lender, 0.0) + amount
        return exposure

    def get_delinquent_rloans(self) -> List[Dict[str, Any]]:
        """
        Get all delinquent mortgages.

        Returns:
            List of mortgages with delinquent status
        """
        return self.find_by_status('Delinquent')

    def get_property_ids_with_rloans(self) -> List[str]:
        """
        Get list of all property IDs that have associated mortgages.

        Returns:
            List of PropertyID strings
        """
        property_ids = []
        for entity in self.load_all():
            prop_id = entity.get('PropertyID')
            if prop_id and prop_id not in property_ids:
                property_ids.append(prop_id)
        return property_ids
