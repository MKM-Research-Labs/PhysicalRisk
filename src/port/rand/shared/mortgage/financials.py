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

"""Mortgage financial calculations and type determination."""

import random
import uuid
from typing import Any, Dict

from .constants import MORTGAGE_TYPES, MORTGAGE_TYPE_WEIGHTS


def determine_mortgage_type(property_info: Dict[str, Any]) -> str:
    """Determine appropriate mortgage type based on property characteristics."""
    if property_info.get("monthly_rent") or property_info.get("rental_history") == "Previously rented":
        return random.choices(["Buy-to-Let", "Residential"], weights=[0.7, 0.3])[0]

    building_residency = property_info.get("building_residency", "").lower()
    if "multi family" in building_residency:
        return random.choices(["Buy-to-Let", "Residential"], weights=[0.5, 0.5])[0]

    occupancy = property_info.get("occupancy_type", "").lower()
    if occupancy == "vacant":
        return random.choices(["Buy-to-Let", "Second Home", "Residential"], weights=[0.4, 0.3, 0.3])[0]

    return random.choices(MORTGAGE_TYPES, weights=MORTGAGE_TYPE_WEIGHTS)[0]


def calculate_mortgage_financials(
    property_value: float,
    mortgage_type: str,
    property_info: Dict[str, Any],
    index: int = 0
) -> Dict[str, Any]:
    """Calculate mortgage financial parameters based on property value and type."""
    if mortgage_type == "Buy-to-Let":
        ltv_ratio = random.triangular(0.6, 0.7, 0.75)
    elif mortgage_type in ["Second Home", "Holiday Home"]:
        ltv_ratio = random.triangular(0.6, 0.7, 0.8)
    else:
        ltv_ratio = random.triangular(0.7, 0.8, 0.95)

    flood_risk = property_info.get("flood_risk", "").lower()
    if "high" in flood_risk:
        ltv_ratio *= 0.95

    loan_amount = property_value * ltv_ratio
    term_years = random.randint(20, 25)
    term_months = term_years * 12

    max_elapsed = term_months - 12
    months_elapsed = random.randint(0, max_elapsed)

    elapsed_ratio = months_elapsed / term_months
    repayment_ratio = elapsed_ratio * (1.1 - 0.2 * elapsed_ratio)
    outstanding_balance = loan_amount * (1 - repayment_ratio)

    current_property_value = property_value * random.uniform(0.95, 1.15)
    current_ltv = outstanding_balance / current_property_value if current_property_value > 0 else ltv_ratio

    base_rate = 0.035
    if mortgage_type == "Buy-to-Let":
        interest_rate = base_rate + random.uniform(0.005, 0.02)
    elif ltv_ratio > 0.9:
        interest_rate = base_rate + random.uniform(0.01, 0.025)
    elif ltv_ratio < 0.7:
        interest_rate = base_rate - random.uniform(0, 0.01)
    else:
        interest_rate = base_rate + random.uniform(-0.005, 0.015)

    if term_months > 0 and interest_rate > 0:
        monthly_rate = interest_rate / 12
        monthly_payment = (loan_amount * monthly_rate * (1 + monthly_rate)**term_months) / \
                         ((1 + monthly_rate)**term_months - 1)
    else:
        monthly_payment = loan_amount / term_months if term_months > 0 else 0

    income_multiple = random.uniform(4.0, 5.5)
    borrower_income = loan_amount / income_multiple

    risk_score = ltv_ratio + random.uniform(0, 0.2)
    is_defaulted = risk_score > 1.05 and random.random() < 0.02
    is_in_arrears = (risk_score > 0.95 and random.random() < 0.05) or is_defaulted

    return {
        "property_value": round(property_value, 2),
        "mortgage_type": mortgage_type,
        "loan_amount": round(loan_amount, 2),
        "ltv_ratio": round(ltv_ratio, 4),
        "term_months": term_months,
        "months_elapsed": months_elapsed,
        "outstanding_balance": round(outstanding_balance, 2),
        "current_ltv": round(current_ltv, 4),
        "interest_rate": round(interest_rate, 4),
        "monthly_payment": round(monthly_payment, 2),
        "borrower_income": round(borrower_income, 2),
        "is_defaulted": is_defaulted,
        "is_in_arrears": is_in_arrears,
        "annual_payment": round(monthly_payment * 12, 2)
    }


def estimate_property_value(property_info: Dict[str, Any]) -> float:
    """Estimate property value based on available information."""
    base_value = 300000

    county = property_info.get("county", "").lower()
    if "london" in county or "greater london" in county:
        base_value *= 2.5
    elif county in ["surrey", "hertfordshire", "buckinghamshire"]:
        base_value *= 1.8
    elif county in ["kent", "essex", "berkshire"]:
        base_value *= 1.5

    bedrooms = property_info.get("number_bedrooms", 3)
    if bedrooms:
        base_value *= (0.7 + bedrooms * 0.15)

    area_sqm = property_info.get("property_area_sqm")
    if area_sqm:
        base_value *= (0.8 + area_sqm / 200)

    construction_year = property_info.get("construction_year")
    if construction_year:
        age = 2025 - construction_year
        if age < 10:
            base_value *= 1.1
        elif age > 50:
            base_value *= 0.9

    base_value *= random.uniform(0.9, 1.1)
    return round(base_value, 2)


def _determine_occupancy_type(mortgage_type: str) -> str:
    """Determine occupancy type based on mortgage type."""
    if mortgage_type == "Buy-to-Let":
        return random.choices(["Investment", "PrimaryResidence"], weights=[0.9, 0.1])[0]
    elif mortgage_type in ["Second Home", "Holiday Home"]:
        return "SecondResidence"
    else:
        return random.choices(["PrimaryResidence", "SecondResidence"], weights=[0.95, 0.05])[0]


def generate_financial_data(property_info: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Generate complete financial data for a mortgage based on property information.

    This is the main entry point called by MortgagePortfolioGenerator.
    """
    mortgage_id = f"MORT-{str(uuid.uuid4())[:8]}"

    property_value = property_info.get('property_value')
    if not property_value or property_value == 0:
        property_value = estimate_property_value(property_info)

    mortgage_type = determine_mortgage_type(property_info)
    financials = calculate_mortgage_financials(property_value, mortgage_type, property_info, index)

    financials['mortgage_id'] = mortgage_id
    financials['property_id'] = property_info.get('property_id', f"PROP-{index}")
    financials['flood_risk'] = property_info.get('flood_risk', 'Low')
    financials['occupancy_type'] = _determine_occupancy_type(mortgage_type)

    return financials
