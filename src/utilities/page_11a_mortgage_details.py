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

# src/utilities/page_11a_mortgage_details.py

"""
Page 11a: Detailed Mortgage Financial Terms
Comprehensive mortgage financial information including all costs, rates, and terms.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class MortgageDetailsPage(BasePage):
    """Generates detailed mortgage financial terms page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate detailed mortgage financial terms page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Detailed Mortgage Financial Terms", self.styles['SectionHeader']))
            
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            financial_data = mortgage_info.get('FinancialTerms', {})
            
            if not financial_data:
                elements.append(Paragraph("No detailed financial terms available.", self.styles['Normal']))
                return elements
            
            # CORE LOAN TERMS
            elements.append(Paragraph("Core Loan Terms", self.styles['SubSectionHeader']))
            
            core_terms_data = [["Financial Term", "Value"]]
            
            # Currency and base amounts
            currency = financial_data.get('currency', 'GBP')
            core_terms_data.append(["Currency", currency])
            
            purchase_value = financial_data.get('PurchaseValue')
            if isinstance(purchase_value, (int, float)):
                core_terms_data.append(["Purchase Value", self._format_currency(purchase_value)])
            
            original_loan = financial_data.get('OriginalLoan')
            if isinstance(original_loan, (int, float)):
                core_terms_data.append(["Original Loan Amount", self._format_currency(original_loan)])
                
                # Calculate loan percentage of purchase value
                if isinstance(purchase_value, (int, float)) and purchase_value > 0:
                    loan_percentage = (original_loan / purchase_value) * 100
                    core_terms_data.append(["Loan as % of Purchase", f"{loan_percentage:.2f}%"])
            
            # Term details
            original_term = financial_data.get('OriginalTerm')
            if isinstance(original_term, (int, float)):
                years = original_term / 12
                core_terms_data.append(["Original Term (Months)", str(int(original_term))])
                core_terms_data.append(["Original Term (Years)", f"{years:.1f} years"])
            
            # Key dates
            disbursal_date = financial_data.get('DisbursalDate')
            if disbursal_date:
                core_terms_data.append(["Disbursal Date", disbursal_date])
            
            maturity_date = financial_data.get('MaturityDate')
            if maturity_date:
                core_terms_data.append(["Maturity Date", maturity_date])
            
            core_terms_table = Table(core_terms_data, colWidths=self.table_widths['two_col'])
            core_terms_table.setStyle(self.table_styles['financial'])
            elements.append(core_terms_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # INTEREST RATES AND PRICING
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Interest Rates & Pricing", self.styles['SubSectionHeader']))
            
            rates_data = [["Rate Component", "Value"]]
            
            # Core interest rates
            original_rate = financial_data.get('OriginalLendingRate')
            if isinstance(original_rate, (int, float)):
                rates_data.append(["Original Lending Rate", self._format_percentage(original_rate)])
            
            original_rate_type = financial_data.get('OriginalRateType')
            if original_rate_type:
                rates_data.append(["Rate Type", original_rate_type])
            
            # Base rate information
            original_boe_base = financial_data.get('OriginalBoEBase')
            if isinstance(original_boe_base, (int, float)):
                rates_data.append(["Original BoE Base Rate", self._format_currency(original_boe_base)])
            
            # Spreads and margins
            original_spread = financial_data.get('OriginalSpread')
            if isinstance(original_spread, (int, float)):
                rates_data.append(["Original Spread", self._format_currency(original_spread)])
            
            hmda_rate_spread = financial_data.get('HMDARateSpread')
            if isinstance(hmda_rate_spread, (int, float)):
                rates_data.append(["HMDA Rate Spread", self._format_currency(hmda_rate_spread)])
            
            # Special rate periods
            initial_fixed_term = financial_data.get('InitialFixedTerm')
            if isinstance(initial_fixed_term, (int, float)):
                rates_data.append(["Initial Fixed Term", f"{int(initial_fixed_term)} months"])
            
            intro_rate_period = financial_data.get('IntroductoryRatePeriod')
            if isinstance(intro_rate_period, (int, float)):
                rates_data.append(["Introductory Rate Period", f"{int(intro_rate_period)} months"])
            
            rates_table = Table(rates_data, colWidths=self.table_widths['two_col'])
            rates_table.setStyle(self.table_styles['financial'])
            elements.append(rates_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # LOAN-TO-VALUE RATIOS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Loan-to-Value Analysis", self.styles['SubSectionHeader']))
            
            ltv_data = [["LTV Metric", "Value"]]
            
            original_ltv = financial_data.get('OriginalLTV')
            if isinstance(original_ltv, (int, float)):
                ltv_percentage = original_ltv * 100 if original_ltv <= 1 else original_ltv
                ltv_data.append(["Original LTV Ratio", f"{ltv_percentage:.2f}%"])
                
                # LTV risk categorization
                if ltv_percentage > 95:
                    ltv_risk = "Very High Risk (>95%)"
                elif ltv_percentage > 90:
                    ltv_risk = "High Risk (90-95%)"
                elif ltv_percentage > 80:
                    ltv_risk = "Medium Risk (80-90%)"
                elif ltv_percentage > 75:
                    ltv_risk = "Low-Medium Risk (75-80%)"
                else:
                    ltv_risk = "Low Risk (<75%)"
                
                ltv_data.append(["LTV Risk Category", ltv_risk])
            
            # Alternative LTV field
            loan_to_value_ratio = financial_data.get('LoanToValueRatio')
            if isinstance(loan_to_value_ratio, (int, float)) and loan_to_value_ratio != original_ltv:
                ltv_alt_percentage = loan_to_value_ratio * 100 if loan_to_value_ratio <= 1 else loan_to_value_ratio
                ltv_data.append(["Alternative LTV Calculation", f"{ltv_alt_percentage:.2f}%"])
            
            ltv_table = Table(ltv_data, colWidths=self.table_widths['two_col'])
            ltv_table.setStyle(self.table_styles['financial'])
            elements.append(ltv_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # DEBT-TO-INCOME ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Debt-to-Income Analysis", self.styles['SubSectionHeader']))
            
            dti_data = [["DTI Metric", "Value"]]
            
            debt_to_income = financial_data.get('DebtToIncomeRatio')
            if isinstance(debt_to_income, (int, float)):
                dti_data.append(["Debt-to-Income Ratio", self._format_currency(debt_to_income)])
                
                # DTI risk assessment (assuming this is a percentage or ratio)
                if debt_to_income > 43:
                    dti_risk = "High Risk - Exceeds recommended 43%"
                elif debt_to_income > 36:
                    dti_risk = "Medium-High Risk - Above conservative 36%"
                elif debt_to_income > 28:
                    dti_risk = "Medium Risk - Above ideal 28%"
                else:
                    dti_risk = "Low Risk - Within conservative guidelines"
                
                dti_data.append(["DTI Risk Assessment", dti_risk])
            
            dti_table = Table(dti_data, colWidths=self.table_widths['two_col'])
            dti_table.setStyle(self.table_styles['financial'])
            elements.append(dti_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating detailed mortgage terms: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements