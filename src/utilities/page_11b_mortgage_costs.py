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

# src/utilities/page_11b_mortgage_costs.py

"""
Page 11b: Mortgage Costs & Fees
Comprehensive breakdown of all mortgage costs, fees, and charges.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class MortgageCostsPage(BasePage):
    """Generates mortgage costs and fees page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate mortgage costs and fees page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Mortgage Costs & Fees", self.styles['SectionHeader']))
            
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            financial_data = mortgage_info.get('FinancialTerms', {})
            
            if not financial_data:
                elements.append(Paragraph("No cost information available.", self.styles['Normal']))
                return elements
            
            # TOTAL LOAN COSTS OVERVIEW
            elements.append(Paragraph("Total Loan Costs Overview", self.styles['SubSectionHeader']))
            
            total_costs_data = [["Cost Category", "Amount"]]
            
            total_loan_costs = financial_data.get('TotalLoanCosts')
            if isinstance(total_loan_costs, (int, float)):
                total_costs_data.append(["Total Loan Costs", self._format_currency(total_loan_costs)])
                
                # Calculate as percentage of loan amount
                original_loan = financial_data.get('OriginalLoan')
                if isinstance(original_loan, (int, float)) and original_loan > 0:
                    cost_percentage = (total_loan_costs / original_loan) * 100
                    total_costs_data.append(["Costs as % of Loan", f"{cost_percentage:.2f}%"])
            
            total_costs_table = Table(total_costs_data, colWidths=self.table_widths['two_col'])
            total_costs_table.setStyle(self.table_styles['financial'])
            elements.append(total_costs_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ORIGINATION AND SETUP COSTS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Origination & Setup Costs", self.styles['SubSectionHeader']))
            
            origination_data = [["Fee Type", "Amount"]]
            
            # Origination charges
            origination_charges = financial_data.get('OriginationCharges')
            if isinstance(origination_charges, (int, float)):
                origination_data.append(["Origination Charges", self._format_currency(origination_charges)])
            
            # Product fee
            product_fee = financial_data.get('ProductFee')
            if isinstance(product_fee, (int, float)):
                origination_data.append(["Product Fee", self._format_currency(product_fee)])
            
            # Discount points
            discount_points = financial_data.get('DiscountPoints')
            if isinstance(discount_points, (int, float)):
                origination_data.append(["Discount Points", self._format_currency(discount_points)])
            
            # Lender credits (negative cost)
            lender_credits = financial_data.get('LenderCredits')
            if isinstance(lender_credits, (int, float)):
                origination_data.append(["Lender Credits", f"-{self._format_currency(lender_credits)}"])
            
            origination_table = Table(origination_data, colWidths=self.table_widths['two_col'])
            origination_table.setStyle(self.table_styles['financial'])
            elements.append(origination_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PENALTY AND RESTRICTION COSTS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Penalties & Restrictions", self.styles['SubSectionHeader']))
            
            penalty_data = [["Penalty Type", "Amount/Period"]]
            
            # Early repayment charge
            early_repayment = financial_data.get('EarlyRepaymentCharge')
            if isinstance(early_repayment, (int, float)):
                penalty_data.append(["Early Repayment Charge", self._format_currency(early_repayment)])
            
            # Prepayment penalty term
            prepayment_penalty_term = financial_data.get('PrepaymentPenaltyTerm')
            if isinstance(prepayment_penalty_term, (int, float)):
                penalty_data.append(["Prepayment Penalty Term", f"{int(prepayment_penalty_term)} months"])
            
            penalty_table = Table(penalty_data, colWidths=self.table_widths['two_col'])
            penalty_table.setStyle(self.table_styles['standard'])
            elements.append(penalty_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # COST ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Cost Analysis", self.styles['SubSectionHeader']))
            
            analysis_data = [["Analysis Factor", "Assessment"]]
            
            # Calculate net upfront costs
            upfront_costs = 0
            cost_items = ['OriginationCharges', 'ProductFee', 'DiscountPoints']
            credits = financial_data.get('LenderCredits', 0)
            
            for item in cost_items:
                value = financial_data.get(item)
                if isinstance(value, (int, float)):
                    upfront_costs += value
            
            net_upfront = upfront_costs - (credits if isinstance(credits, (int, float)) else 0)
            analysis_data.append(["Net Upfront Costs", self._format_currency(net_upfront)])
            
            # Cost burden analysis
            original_loan = financial_data.get('OriginalLoan')
            if isinstance(original_loan, (int, float)) and original_loan > 0:
                cost_burden = (net_upfront / original_loan) * 100
                analysis_data.append(["Cost Burden (% of Loan)", f"{cost_burden:.2f}%"])
                
                # Cost assessment
                if cost_burden > 5:
                    cost_assessment = "High - Significant upfront costs"
                elif cost_burden > 3:
                    cost_assessment = "Medium-High - Above average costs"
                elif cost_burden > 1.5:
                    cost_assessment = "Medium - Typical costs"
                elif cost_burden > 0.5:
                    cost_assessment = "Low-Medium - Below average costs"
                else:
                    cost_assessment = "Low - Minimal costs"
                
                analysis_data.append(["Cost Assessment", cost_assessment])
            
            # Discount points value analysis
            if isinstance(discount_points, (int, float)) and isinstance(original_rate, (int, float)):
                # Rough estimate of rate reduction (typically 0.25% per point)
                estimated_points = discount_points / (original_loan * 0.01) if original_loan > 0 else 0
                if estimated_points > 0:
                    analysis_data.append(["Estimated Points Purchased", f"{estimated_points:.2f} points"])
                    analysis_data.append(["Estimated Rate Reduction", f"~{estimated_points * 0.25:.2f}%"])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating mortgage costs: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements