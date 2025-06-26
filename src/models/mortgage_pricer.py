# Copyright (c) 2025 MKM Research Labs. All rights reserved.
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
"""
Mortgage Pricer

This module provides mortgage pricing functionality that considers credit risk,
affordability metrics, and term structure. It integrates with flood risk assessments
to adjust pricing based on property-level risk.
"""

import numpy as np
from scipy import interpolate
import datetime
import pandas as pd
from typing import Tuple, Dict, Any, Optional, List, Union


class MortgagePricer:
    """
    Mortgage pricing engine that calculates present value of mortgages considering
    credit risk, affordability, and external risk factors like flood risk.
    """
    
    def __init__(self, principal: float, annual_interest_rate: float, term_years: int):
        """
        Initialize the mortgage pricer.
        
        Args:
            principal: Loan principal amount
            annual_interest_rate: Annual interest rate (percentage)
            term_years: Loan term in years
        """
        self.principal = principal
        self.annual_interest_rate = annual_interest_rate
        self.term_years = term_years
        self.tax_rate = 0.20  # Default 20% tax rate
        
        # Initialize credit spread function
        self.credit_spread_function = self._create_credit_spread_function()
    
    def _create_credit_spread_function(self):
        """
        Create interpolation function for credit spreads based on affordability ratios.
        
        Returns:
            Function that interpolates credit spreads based on affordability
        """
        # Affordability ratio points (total cost / after-tax income)
        affordability_ratios = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        # Corresponding credit spreads (annual)
        credit_spreads = [0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.18, 0.25, 0.35]
        
        return interpolate.interp1d(
            affordability_ratios, credit_spreads, 
            kind='linear', fill_value='extrapolate'
        )
    
    def calculate_monthly_payment(self) -> float:
        """
        Calculate standard monthly mortgage payment.
        
        Returns:
            Monthly payment amount
        """
        monthly_rate = self.annual_interest_rate / 12 / 100
        num_payments = self.term_years * 12
        
        if monthly_rate == 0:
            return self.principal / num_payments
        
        payment = (self.principal * monthly_rate * (1 + monthly_rate)**num_payments) / \
                  ((1 + monthly_rate)**num_payments - 1)
        
        return payment
    
    def calculate_total_cost(self) -> float:
        """
        Calculate total cost of the mortgage over its lifetime.
        
        Returns:
            Total amount paid over the loan term
        """
        monthly_payment = self.calculate_monthly_payment()
        return monthly_payment * self.term_years * 12
    
    def calculate_credit_spread(self, 
                              gross_annual_income: float, 
                              annual_payment: float, 
                              insurance_rate: float, 
                              property_value: float, 
                              original_maturity: float, 
                              current_term: float,
                              tax_rate: Optional[float] = None,
                              debug: bool = False) -> float:
        """
        Calculate credit spread based on borrower affordability and loan characteristics.
        
        Args:
            gross_annual_income: Borrower's gross annual income
            annual_payment: Annual mortgage payment
            insurance_rate: Insurance rate (as decimal of property value)
            property_value: Current property value
            original_maturity: Original loan term in years
            current_term: Remaining loan term in years
            tax_rate: Tax rate (optional, uses instance default if not provided)
            debug: Whether to print debug information
            
        Returns:
            Credit spread as decimal (e.g., 0.05 = 5%)
        """
        # Use provided tax rate or instance default
        effective_tax_rate = tax_rate if tax_rate is not None else self.tax_rate
        
        # Handle edge case of zero income
        if gross_annual_income <= 0:
            if debug:
                print("Warning: Zero/negative income, using default high spread")
            return 0.15  # 15% default spread for missing income data
        
        # Calculate affordability metrics
        after_tax_income = gross_annual_income * (1 - effective_tax_rate)
        annual_insurance_cost = insurance_rate * property_value
        total_annual_cost = annual_payment + annual_insurance_cost
        affordability_ratio = total_annual_cost / after_tax_income
        
        # Cap affordability ratio to reasonable bounds
        affordability_ratio = max(0.1, min(affordability_ratio, 1.0))
        
        # Calculate base credit spread
        base_spread = self.credit_spread_function(affordability_ratio)
        
        # Apply term structure adjustment
        original_maturity = max(original_maturity, 1)  # Minimum 1 year
        current_term = max(current_term, 0.5)          # Minimum 6 months
        
        # Term factor: longer remaining terms get slightly higher spreads
        term_factor = 1 + (current_term - original_maturity/2) / 100
        credit_spread = base_spread * term_factor
        
        if debug:
            print(f"\nCredit Spread Calculation:")
            print(f"  Gross Income: £{gross_annual_income:,.2f}")
            print(f"  After-tax Income: £{after_tax_income:,.2f}")
            print(f"  Annual Payment: £{annual_payment:,.2f}")
            print(f"  Annual Insurance: £{annual_insurance_cost:,.2f}")
            print(f"  Total Annual Cost: £{total_annual_cost:,.2f}")
            print(f"  Affordability Ratio: {affordability_ratio:.3f}")
            print(f"  Base Spread: {base_spread:.4f}")
            print(f"  Term Factor: {term_factor:.4f}")
            print(f"  Final Credit Spread: {credit_spread:.4f}")
        
        return max(0.001, credit_spread)  # Minimum 0.1% spread
    
    def price_mortgage(self, 
                      loan_amount: float, 
                      property_value: float, 
                      gross_annual_income: float, 
                      interest_rate: float, 
                      insurance_rate: float, 
                      original_maturity: float, 
                      current_term: float, 
                      recovery_haircut: float,
                      tax_rate: Optional[float] = None,
                      debug: bool = False) -> Dict[str, Any]:
        """
        Price a mortgage considering credit risk and expected losses.
        
        Args:
            loan_amount: Outstanding mortgage amount
            property_value: Current property value
            gross_annual_income: Borrower's gross annual income
            interest_rate: Base interest rate (as decimal)
            insurance_rate: Insurance rate (as decimal of property value)
            original_maturity: Original mortgage term in years
            current_term: Remaining term in years
            recovery_haircut: Recovery haircut in default (as decimal)
            tax_rate: Tax rate (optional)
            debug: Whether to print detailed calculations
            
        Returns:
            Dictionary containing pricing results and intermediate calculations
        """
        try:
            # Input validation and normalization
            loan_amount = max(loan_amount, 1)
            property_value = max(property_value, 1)
            gross_annual_income = max(gross_annual_income, 1)
            interest_rate = max(interest_rate, 0.001)  # Minimum 0.1%
            insurance_rate = max(insurance_rate, 0)
            original_maturity = max(original_maturity, 1)
            current_term = max(min(current_term, original_maturity), 0.5)
            recovery_haircut = max(min(recovery_haircut, 0.95), 0)  # Cap at 95%
            
            effective_tax_rate = tax_rate if tax_rate is not None else self.tax_rate
            
            # Calculate payment schedule
            n_periods = int(current_term * 12)
            monthly_rate = interest_rate / 12
            
            if monthly_rate == 0:
                monthly_payment = loan_amount / n_periods
            else:
                monthly_payment = loan_amount * monthly_rate / (1 - (1 + monthly_rate)**(-n_periods))
            
            annual_payment = monthly_payment * 12
            
            if debug:
                print(f"\nMortgage Pricing Inputs:")
                print(f"  Loan Amount: £{loan_amount:,.2f}")
                print(f"  Property Value: £{property_value:,.2f}")
                print(f"  Interest Rate: {interest_rate*100:.2f}%")
                print(f"  Current Term: {current_term:.1f} years")
                print(f"  Monthly Payment: £{monthly_payment:,.2f}")
                print(f"  Annual Payment: £{annual_payment:,.2f}")
            
            # Calculate credit spread
            credit_spread = self.calculate_credit_spread(
                gross_annual_income, annual_payment, insurance_rate, 
                property_value, original_maturity, current_term, 
                effective_tax_rate, debug
            )
            
            # Initialize time series arrays
            outstanding_balance = np.zeros(n_periods + 1)
            outstanding_balance[0] = loan_amount
            
            credit_spreads = np.full(n_periods + 1, credit_spread)
            hazard_rates = np.zeros(n_periods + 1)
            survival_probs = np.zeros(n_periods + 1)
            survival_probs[0] = 1.0
            lgds = np.zeros(n_periods + 1)  # Loss Given Default
            
            # Calculate time series for each period
            for i in range(1, n_periods + 1):
                # Update outstanding balance
                if i <= n_periods:
                    interest_payment = outstanding_balance[i-1] * monthly_rate
                    principal_payment = monthly_payment - interest_payment
                    outstanding_balance[i] = max(0, outstanding_balance[i-1] - principal_payment)
                
                # Calculate Loss Given Default
                recovery_value = (1 - recovery_haircut) * property_value
                lgds[i] = max(0, outstanding_balance[i] - recovery_value)
                
                # Calculate hazard rate (probability of default this period)
                hazard_rates[i] = 1 - np.exp(-credit_spreads[i] / 12)
                
                # Calculate survival probability
                survival_probs[i] = survival_probs[i-1] * (1 - hazard_rates[i-1])
            
            # Calculate expected cashflows and losses
            expected_cashflows = np.zeros(n_periods)
            expected_losses = np.zeros(n_periods)
            
            for i in range(n_periods):
                period_idx = i + 1
                
                # Probability of default in this period
                default_prob = max(0, survival_probs[i] - survival_probs[period_idx])
                
                # Expected cashflow: payment if survives + recovery if defaults
                expected_cashflows[i] = (monthly_payment * survival_probs[period_idx] + 
                                       (outstanding_balance[i] - lgds[period_idx]) * default_prob)
                
                # Expected loss in this period
                expected_losses[i] = lgds[period_idx] * default_prob
            
            # Calculate present values
            periods_array = np.arange(1, n_periods + 1)
            discount_factors = (1 + interest_rate/12) ** (-periods_array)
            
            pv_cashflows = np.sum(expected_cashflows * discount_factors)
            pv_losses = np.sum(expected_losses * discount_factors)
            mortgage_value = pv_cashflows - pv_losses
            
            if debug:
                print(f"\nPricing Results:")
                print(f"  Credit Spread: {credit_spread*100:.3f}%")
                print(f"  PV Expected Cashflows: £{pv_cashflows:,.2f}")
                print(f"  PV Expected Losses: £{pv_losses:,.2f}")
                print(f"  Mortgage Fair Value: £{mortgage_value:,.2f}")
                print(f"  Discount to Par: £{loan_amount - mortgage_value:,.2f}")
                print(f"  Discount Percentage: {((loan_amount - mortgage_value)/loan_amount)*100:.2f}%")
            
            # Compile comprehensive results
            return {
                'mortgage_value': mortgage_value,
                'credit_spread': credit_spread,
                'annual_payment': annual_payment,
                'monthly_payment': monthly_payment,
                'outstanding_balance': outstanding_balance,
                'hazard_rates': hazard_rates,
                'lgds': lgds,
                'survival_probs': survival_probs,
                'expected_cashflows': expected_cashflows,
                'expected_losses': expected_losses,
                'pv_cashflows': pv_cashflows,
                'pv_losses': pv_losses,
                'discount_to_par': loan_amount - mortgage_value,
                'discount_percentage': ((loan_amount - mortgage_value)/loan_amount)*100,
                'ltv_ratio': loan_amount / property_value,
                'affordability_ratio': (annual_payment + insurance_rate * property_value) / 
                                     (gross_annual_income * (1 - effective_tax_rate))
            }
            
        except Exception as e:
            if debug:
                print(f"Error in mortgage pricing: {str(e)}")
                import traceback
                traceback.print_exc()
            
            # Return fallback values in case of error
            return {
                'mortgage_value': loan_amount * 0.9,  # Conservative 10% haircut
                'credit_spread': 0.10,                # 10% default spread
                'annual_payment': loan_amount * 0.08, # Rough 8% annual cost
                'monthly_payment': loan_amount * 0.08 / 12,
                'outstanding_balance': np.array([loan_amount]),
                'hazard_rates': np.array([0.05]),
                'lgds': np.array([loan_amount * 0.3]),
                'survival_probs': np.array([1.0]),
                'expected_cashflows': np.array([loan_amount * 0.08]),
                'expected_losses': np.array([loan_amount * 0.02]),
                'pv_cashflows': loan_amount,
                'pv_losses': loan_amount * 0.1,
                'discount_to_par': loan_amount * 0.1,
                'discount_percentage': 10.0,
                'ltv_ratio': loan_amount / property_value if property_value > 0 else 1.0,
                'affordability_ratio': 0.5,  # Default assumption
                'error': str(e)
            }
    
    def calculate_loan_to_value_impact(self, loan_amount: float, property_value: float) -> float:
        """
        Calculate LTV-based risk adjustment factor.
        
        Args:
            loan_amount: Outstanding loan amount
            property_value: Current property value
            
        Returns:
            Risk adjustment factor (1.0 = no adjustment, >1.0 = higher risk)
        """
        ltv = loan_amount / property_value if property_value > 0 else 1.0
        
        # LTV-based risk adjustments
        if ltv > 0.95:
            return 1.5      # Very high LTV
        elif ltv > 0.9:
            return 1.3      # High LTV
        elif ltv > 0.8:
            return 1.1      # Moderate LTV
        else:
            return 1.0      # Standard LTV
    
    def batch_price_mortgages(self, mortgage_portfolio: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Price a batch of mortgages efficiently.
        
        Args:
            mortgage_portfolio: List of mortgage dictionaries with required fields
            
        Returns:
            List of pricing results for each mortgage
        """
        results = []
        
        for i, mortgage in enumerate(mortgage_portfolio):
            try:
                # Extract mortgage parameters
                pricing_result = self.price_mortgage(
                    loan_amount=mortgage.get('loan_amount', 0),
                    property_value=mortgage.get('property_value', 0),
                    gross_annual_income=mortgage.get('gross_annual_income', 50000),
                    interest_rate=mortgage.get('interest_rate', 0.035),
                    insurance_rate=mortgage.get('insurance_rate', 0.002),
                    original_maturity=mortgage.get('original_maturity', 30),
                    current_term=mortgage.get('current_term', 30),
                    recovery_haircut=mortgage.get('recovery_haircut', 0.2)
                )
                
                # Add mortgage identifier
                pricing_result['mortgage_id'] = mortgage.get('mortgage_id', f'MORTGAGE_{i}')
                pricing_result['property_id'] = mortgage.get('property_id', f'PROPERTY_{i}')
                
                results.append(pricing_result)
                
            except Exception as e:
                # Add error result for failed pricing
                results.append({
                    'mortgage_id': mortgage.get('mortgage_id', f'MORTGAGE_{i}'),
                    'property_id': mortgage.get('property_id', f'PROPERTY_{i}'),
                    'error': str(e),
                    'mortgage_value': 0
                })
        
        return results


# Utility functions for mortgage analysis
def calculate_portfolio_metrics(pricing_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate portfolio-level metrics from individual mortgage pricing results.
    
    Args:
        pricing_results: List of mortgage pricing results
        
    Returns:
        Dictionary of portfolio metrics
    """
    # Filter out error results
    valid_results = [r for r in pricing_results if 'error' not in r]
    
    if not valid_results:
        return {'error': 'No valid pricing results'}
    
    # Extract values
    mortgage_values = [r['mortgage_value'] for r in valid_results]
    credit_spreads = [r['credit_spread'] for r in valid_results]
    discount_percentages = [r['discount_percentage'] for r in valid_results]
    ltv_ratios = [r['ltv_ratio'] for r in valid_results]
    
    return {
        'total_mortgage_value': sum(mortgage_values),
        'average_mortgage_value': np.mean(mortgage_values),
        'total_mortgages': len(valid_results),
        'average_credit_spread': np.mean(credit_spreads),
        'median_credit_spread': np.median(credit_spreads),
        'average_discount_percentage': np.mean(discount_percentages),
        'total_discount_amount': sum(r.get('discount_to_par', 0) for r in valid_results),
        'average_ltv': np.mean(ltv_ratios),
        'high_risk_mortgages': sum(1 for r in valid_results if r['credit_spread'] > 0.1),
        'error_count': len(pricing_results) - len(valid_results)
    }


# Example usage
if __name__ == "__main__":
    # Example mortgage pricing
    pricer = MortgagePricer(principal=400000, annual_interest_rate=3.5, term_years=30)
    
    # Price a single mortgage
    result = pricer.price_mortgage(
        loan_amount=400000,
        property_value=500000,
        gross_annual_income=75000,
        interest_rate=0.035,
        insurance_rate=0.002,
        original_maturity=30,
        current_term=25,
        recovery_haircut=0.25,
        debug=True
    )
    
    print(f"\nMortgage pricing result:")
    print(f"Fair value: £{result['mortgage_value']:,.2f}")
    print(f"Credit spread: {result['credit_spread']*100:.2f}%")
    print(f"Discount to par: {result['discount_percentage']:.2f}%")