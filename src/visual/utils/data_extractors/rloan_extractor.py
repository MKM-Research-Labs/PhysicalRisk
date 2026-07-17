# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Residential-loan data extraction utilities.

NOTE: data-shape strings ('RLoan', 'RLoanID', 'loans') and the
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
        mort_data = mortgage.get('RLoan', mortgage)

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

        rloan_info = {
            # Header section
            'mortgage_id': header.get('RLoanID'),
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
        return {k: v for k, v in rloan_info.items() if v is not None}

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


def build_rloan_lookup(rloan_data: Union[Dict, List]) -> Dict[str, Dict]:
    """
    Build a lookup dictionary of residential loans by property ID.

    Args:
        rloan_data: Dictionary or list of residential-loan data

    Returns:
        Dictionary mapping property IDs to residential-loan information
    """
    lookup = {}

    logger.debug("Building rloan lookup from data of type: %s", type(rloan_data))

    # Handle different possible formats of rloan data
    mortgages = _normalize_rloan_list(rloan_data)

    if isinstance(mortgages, list):
        for mortgage in mortgages:
            try:
                rloan_info = extract_rloan_info(mortgage)
                if rloan_info and rloan_info.get('property_id'):
                    lookup[rloan_info['property_id']] = rloan_info
            except Exception as e:
                logger.error("Error processing mortgage: %s", e)

    logger.debug("Built rloan lookup with %d entries", len(lookup))
    return lookup


def _normalize_rloan_list(rloan_data: Union[Dict, List]) -> List:
    """Normalize residential-loan data to a list format."""
    if isinstance(rloan_data, dict):
        if 'loans' in rloan_data:
            return rloan_data['loans']
        elif 'Mortgages' in rloan_data:
            return rloan_data['Mortgages']
        elif 'mortgage_portfolio' in rloan_data:
            return rloan_data['mortgage_portfolio']
        else:
            # Assume it's a single mortgage wrapped in dict
            return [rloan_data]
    elif isinstance(rloan_data, list):
        return rloan_data
    else:
        logger.warning("Unexpected mortgage data type: %s", type(rloan_data))
        return []
