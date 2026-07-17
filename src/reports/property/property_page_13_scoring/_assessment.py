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

"""Comprehensive and property-only risk assessment scoring (page 13)."""

from typing import Any, Dict

from ._helpers import (
    generate_monitoring_schedule,
    generate_recommendations,
    identify_key_factors,
)


def comprehensive_risk_assessment(property_data: Dict[str, Any],
                                  rloan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive risk assessment with both property and mortgage data."""

    # Extract key data
    rloan_info = rloan_data.get('RLoan', rloan_data)
    property_flood_risk = (property_data.get('PropertyHeader', {})
                         .get('RiskAssessment', {})
                         .get('OverallFloodRisk', 'Unknown'))

    current_status = rloan_info.get('CurrentStatus', {})
    borrower_details = rloan_info.get('BorrowerDetails', {})

    categories = {}

    # 1. PROPERTY FLOOD RISK (15% weight)
    flood_score = {
        'Very Low': 1, 'Low': 2, 'Medium': 3, 'High': 4, 'Very High': 5
    }.get(property_flood_risk, 3)

    categories['Property Flood Risk'] = {
        'score': flood_score,
        'weight': 15,
        'impact': f"{property_flood_risk} flood risk"
    }

    # 2. CURRENT LTV RISK (20% weight)
    current_ltv = current_status.get('CurrentLTV', 0)
    if isinstance(current_ltv, (int, float)):
        ltv_percentage = current_ltv * 100 if current_ltv <= 1 else current_ltv
        if ltv_percentage > 95:
            ltv_score, ltv_impact = 5, "Very High LTV (>95%)"
        elif ltv_percentage > 90:
            ltv_score, ltv_impact = 4, "High LTV (90-95%)"
        elif ltv_percentage > 80:
            ltv_score, ltv_impact = 3, "Medium LTV (80-90%)"
        elif ltv_percentage > 70:
            ltv_score, ltv_impact = 2, "Low-Medium LTV (70-80%)"
        else:
            ltv_score, ltv_impact = 1, "Low LTV (<70%)"
    else:
        ltv_score, ltv_impact = 3, "Unknown LTV"

    categories['Current LTV Risk'] = {
        'score': ltv_score,
        'weight': 20,
        'impact': ltv_impact
    }

    # 3. PAYMENT PERFORMANCE (25% weight)
    in_arrears = current_status.get('InArrearsFlag', False)
    missed_payments = current_status.get('MissedPayments12M', 0)

    if in_arrears:
        payment_score, payment_impact = 5, "Currently in arrears"
    elif isinstance(missed_payments, (int, float)) and missed_payments > 3:
        payment_score, payment_impact = 4, f"Multiple missed payments ({int(missed_payments)})"
    elif isinstance(missed_payments, (int, float)) and missed_payments > 0:
        payment_score, payment_impact = 3, f"Some missed payments ({int(missed_payments)})"
    else:
        payment_score, payment_impact = 1, "Good payment history"

    categories['Payment Performance'] = {
        'score': payment_score,
        'weight': 25,
        'impact': payment_impact
    }

    # 4. BORROWER CREDIT RISK (15% weight)
    credit_score = borrower_details.get('BorrowerCreditScore')
    if isinstance(credit_score, (int, float)):
        if credit_score >= 800:
            credit_risk_score, credit_impact = 1, f"Excellent credit ({int(credit_score)})"
        elif credit_score >= 740:
            credit_risk_score, credit_impact = 2, f"Very good credit ({int(credit_score)})"
        elif credit_score >= 670:
            credit_risk_score, credit_impact = 3, f"Good credit ({int(credit_score)})"
        elif credit_score >= 580:
            credit_risk_score, credit_impact = 4, f"Fair credit ({int(credit_score)})"
        else:
            credit_risk_score, credit_impact = 5, f"Poor credit ({int(credit_score)})"
    else:
        credit_risk_score, credit_impact = 3, "Credit score unknown"

    categories['Borrower Credit Risk'] = {
        'score': credit_risk_score,
        'weight': 15,
        'impact': credit_impact
    }

    # 5. INTEREST RATE RISK (10% weight)
    current_rate = current_status.get('CurrentLendingRate', 0)
    if isinstance(current_rate, (int, float)) and current_rate > 0:
        if current_rate > 7:
            rate_score, rate_impact = 4, f"High rate ({current_rate:.2f}%)"
        elif current_rate > 5:
            rate_score, rate_impact = 3, f"Elevated rate ({current_rate:.2f}%)"
        elif current_rate > 3:
            rate_score, rate_impact = 2, f"Moderate rate ({current_rate:.2f}%)"
        else:
            rate_score, rate_impact = 1, f"Low rate ({current_rate:.2f}%)"
    else:
        rate_score, rate_impact = 3, "Unknown rate"

    categories['Interest Rate Risk'] = {
        'score': rate_score,
        'weight': 10,
        'impact': rate_impact
    }

    # 6. DEBT-TO-INCOME RISK (15% weight)
    borrower_income = borrower_details.get('BorrowerIncome', 0)
    current_payment = current_status.get('CurrentPayment', 0)

    if isinstance(borrower_income, (int, float)) and isinstance(current_payment, (int, float)) and borrower_income > 0:
        monthly_income = borrower_income / 12
        dti_ratio = (current_payment / monthly_income) * 100

        if dti_ratio > 43:
            dti_score, dti_impact = 5, f"Very high DTI ({dti_ratio:.1f}%)"
        elif dti_ratio > 36:
            dti_score, dti_impact = 4, f"High DTI ({dti_ratio:.1f}%)"
        elif dti_ratio > 28:
            dti_score, dti_impact = 3, f"Moderate DTI ({dti_ratio:.1f}%)"
        else:
            dti_score, dti_impact = 2, f"Good DTI ({dti_ratio:.1f}%)"
    else:
        dti_score, dti_impact = 3, "DTI cannot be calculated"

    categories['Debt-to-Income Risk'] = {
        'score': dti_score,
        'weight': 15,
        'impact': dti_impact
    }

    # Calculate overall assessment
    total_weighted_score = sum(cat['score'] * cat['weight'] for cat in categories.values())
    total_weight = sum(cat['weight'] for cat in categories.values())
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
    overall_percentage = (overall_score / 5) * 100

    # Determine risk level and color
    if overall_percentage >= 85:
        level, color = "CRITICAL RISK", "RED"
    elif overall_percentage >= 70:
        level, color = "HIGH RISK", "ORANGE"
    elif overall_percentage >= 55:
        level, color = "MODERATE-HIGH RISK", "YELLOW"
    elif overall_percentage >= 40:
        level, color = "MODERATE RISK", "LIGHT GREEN"
    else:
        level, color = "LOW RISK", "GREEN"

    # Generate key factors, recommendations, and monitoring
    key_factors = identify_key_factors(categories)
    recommendations = generate_recommendations(categories, overall_score)
    monitoring = generate_monitoring_schedule(overall_score)

    return {
        'categories': categories,
        'overall_score': overall_score,
        'overall_percentage': overall_percentage,
        'overall_level': level,
        'overall_color': color,
        'key_factors': key_factors,
        'recommendations': recommendations,
        'monitoring': monitoring
    }


def property_risk_assessment(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform property-only risk assessment."""
    # Simplified version for property-only analysis
    flood_risk = (property_data.get('PropertyHeader', {})
                 .get('RiskAssessment', {})
                 .get('OverallFloodRisk', 'Unknown'))

    categories = {
        'Property Flood Risk': {
            'score': {'Very Low': 1, 'Low': 2, 'Medium': 3, 'High': 4, 'Very High': 5}.get(flood_risk, 3),
            'weight': 40,
            'impact': f"{flood_risk} flood risk"
        },
        'Property Protection': {
            'score': 3,  # Would assess based on protection measures
            'weight': 30,
            'impact': "Protection measures assessment needed"
        },
        'Location Risk': {
            'score': 2,  # Would assess based on location factors
            'weight': 30,
            'impact': "Standard location risk"
        }
    }

    # Calculate overall assessment
    total_weighted_score = sum(cat['score'] * cat['weight'] for cat in categories.values())
    total_weight = sum(cat['weight'] for cat in categories.values())
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
    overall_percentage = (overall_score / 5) * 100

    if overall_percentage >= 70:
        level, color = "HIGH RISK", "ORANGE"
    elif overall_percentage >= 50:
        level, color = "MEDIUM RISK", "YELLOW"
    else:
        level, color = "LOW RISK", "GREEN"

    return {
        'categories': categories,
        'overall_score': overall_score,
        'overall_percentage': overall_percentage,
        'overall_level': level,
        'overall_color': color,
        'key_factors': {'Primary Risk': flood_risk},
        'recommendations': ['Regular monitoring advised', 'Consider flood protection measures'],
        'monitoring': {'Property condition': 'Annual', 'Flood risk updates': 'Annual'}
    }
