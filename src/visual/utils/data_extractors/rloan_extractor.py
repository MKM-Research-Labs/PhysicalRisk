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

"""Residential-loan data extraction utilities.

NOTE: data-shape strings ('Mortgage', 'MortgageID', 'mortgages') and the
result-dict keys ('mortgage_id', 'mortgage_provider', ...) still match the
currently generated data; they are renamed in the later data-key stage.
"""

import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def extract_rloan_info(mortgage: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract mortgage information from mortgage data.

    Args:
        mortgage: Raw mortgage data dictionary

    Returns:
        Structured mortgage data or None if extraction fails
    """
    try:
        # Handle nested structure
        mort_data = mortgage.get('Mortgage', mortgage)

        # Extract the Header section
        header = mort_data.get('Header', {})
        property_id = header.get('PropertyID')

        if not property_id:
            logger.warning("PropertyID is missing or empty in mortgage data")
            return None

        # Extract financial terms
        financial_terms = mort_data.get('FinancialTerms', {})
        application = mort_data.get('Application', {})

        # Try different field names for term years
        term_years = _extract_term_years(financial_terms)

        mortgage_info = {
            # Header section
            'mortgage_id': header.get('MortgageID'),
            'property_id': property_id,
            'uprn': header.get('UPRN'),

            # Financial terms
            'original_loan': financial_terms.get('OriginalLoan'),
            'current_balance': financial_terms.get('CurrentBalance'),
            'original_lending_rate': financial_terms.get('OriginalLendingRate'),
            'current_rate': financial_terms.get('CurrentRate'),
            'loan_to_value_ratio': financial_terms.get('LoanToValueRatio'),
            'term_years': term_years,
            'monthly_payment': financial_terms.get('MonthlyPayment'),

            # Application details
            'mortgage_provider': application.get('MortgageProvider'),
            'application_date': application.get('ApplicationDate'),
            'completion_date': application.get('CompletionDate'),

            # Store original structure for backward compatibility
            'Header': header,
            'FinancialTerms': financial_terms,
            'Application': application
        }

        # Remove None values
        return {k: v for k, v in mortgage_info.items() if v is not None}

    except Exception as e:
        logger.error("Error extracting mortgage info: %s", e)
        return None


def _extract_term_years(financial_terms: Dict[str, Any]) -> Optional[float]:
    """Extract term years from financial terms, trying multiple field names."""
    term_fields = ['TermYears', 'Term', 'LoanTerm', 'OriginalTerm']

    for field in term_fields:
        if field in financial_terms:
            term_years = financial_terms.get(field)
            if term_years is not None:
                # If term is in months, convert to years
                if field == 'OriginalTerm' and term_years > 100:
                    return term_years / 12
                return term_years

    return None


def build_rloan_lookup(mortgage_data: Union[Dict, List]) -> Dict[str, Dict]:
    """
    Build a lookup dictionary of residential loans by property ID.

    Args:
        mortgage_data: Dictionary or list of residential-loan data

    Returns:
        Dictionary mapping property IDs to residential-loan information
    """
    lookup = {}

    logger.debug("Building rloan lookup from data of type: %s", type(mortgage_data))

    # Handle different possible formats of rloan data
    mortgages = _normalize_rloan_list(mortgage_data)

    if isinstance(mortgages, list):
        for mortgage in mortgages:
            try:
                mortgage_info = extract_rloan_info(mortgage)
                if mortgage_info and mortgage_info.get('property_id'):
                    lookup[mortgage_info['property_id']] = mortgage_info
            except Exception as e:
                logger.error("Error processing mortgage: %s", e)

    logger.debug("Built rloan lookup with %d entries", len(lookup))
    return lookup


def _normalize_rloan_list(mortgage_data: Union[Dict, List]) -> List:
    """Normalize residential-loan data to a list format."""
    if isinstance(mortgage_data, dict):
        if 'mortgages' in mortgage_data:
            return mortgage_data['mortgages']
        elif 'Mortgages' in mortgage_data:
            return mortgage_data['Mortgages']
        elif 'mortgage_portfolio' in mortgage_data:
            return mortgage_data['mortgage_portfolio']
        else:
            # Assume it's a single mortgage wrapped in dict
            return [mortgage_data]
    elif isinstance(mortgage_data, list):
        return mortgage_data
    else:
        logger.warning("Unexpected mortgage data type: %s", type(mortgage_data))
        return []
