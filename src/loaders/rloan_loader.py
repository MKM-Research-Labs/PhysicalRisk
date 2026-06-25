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

    def _load_document(self) -> Optional[Dict[str, Any]]:
        """Read the loan portfolio through the database seam (active catchment)."""
        import database
        return database.get_loan_portfolio(database.active_catchment())

    @staticmethod
    def _rl(entity: Dict[str, Any]) -> Dict[str, Any]:
        """The nested RLoan body (Header/Application/FinancialTerms/...), falling back
        to the entity itself for legacy flat records."""
        return entity.get('RLoan', entity)

    def get_entity_id(self, entity: Dict[str, Any]) -> Optional[str]:
        """Extract RLoanID (nested RLoan.Header.RLoanID, or legacy flat)."""
        return self._rl(entity).get('Header', {}).get('RLoanID') or entity.get('RLoanID')

    def get_entity_summary(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Create mortgage summary for listing (reads the nested RLoan structure)."""
        rl = self._rl(entity)
        hdr, fin, cur = (rl.get('Header', {}), rl.get('FinancialTerms', {}),
                         rl.get('CurrentStatus', {}))
        return {
            'mortgageId': hdr.get('RLoanID') or entity.get('RLoanID'),
            'propertyId': hdr.get('PropertyID') or entity.get('PropertyID'),
            'loanAmount': fin.get('OriginalLoan', entity.get('LoanAmount')),
            'interestRate': fin.get('OriginalLendingRate', entity.get('InterestRate')),
            'loanType': rl.get('Features', {}).get('MortgageType', entity.get('LoanType')),
            'lender': rl.get('Application', {}).get('MortgageProvider',
                                                    entity.get('Lender')),
            'status': cur.get('AccountStatus', entity.get('Status')),
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
            entity_lender = self._rl(entity).get('Application', {}).get(
                'MortgageProvider', entity.get('Lender', '')) or ''
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
            entity_status = self._rl(entity).get('CurrentStatus', {}).get(
                'AccountStatus', entity.get('Status', '')) or ''
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
            amount = self._rl(entity).get('FinancialTerms', {}).get(
                'OriginalLoan', entity.get('LoanAmount', 0))
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
            rl = self._rl(entity)
            lender = rl.get('Application', {}).get('MortgageProvider',
                                                   entity.get('Lender', 'Unknown'))
            amount = rl.get('FinancialTerms', {}).get('OriginalLoan',
                                                      entity.get('LoanAmount', 0))
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
            prop_id = (self._rl(entity).get('Header', {}).get('PropertyID')
                       or entity.get('PropertyID'))
            if prop_id and prop_id not in property_ids:
                property_ids.append(prop_id)
        return property_ids
