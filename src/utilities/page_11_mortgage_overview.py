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

# src/utilities/page_11_mortgage_overview.py

"""
Page 11: Mortgage Overview
Handles mortgage identification, application details, and basic terms.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class MortgageOverviewPage(BasePage):
    """Generates mortgage overview page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate mortgage overview page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Mortgage Overview", self.styles['SectionHeader']))
            
            # Handle nested mortgage structure
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            
            # MORTGAGE IDENTIFICATION
            header_data = mortgage_info.get('Header', {})
            if header_data:
                elements.append(Paragraph("Mortgage Identification", self.styles['SubSectionHeader']))
                
                header_table_data = [["Mortgage Details", "Value"]]
                
                key_fields = ['MortgageID', 'PropertyID', 'UPRN']
                for field in key_fields:
                    value = header_data.get(field)
                    if value:
                        header_table_data.append([self._format_field_name(field), str(value)])
                
                header_table = Table(header_table_data, colWidths=self.table_widths['two_col'])
                header_table.setStyle(self.table_styles['standard'])
                elements.append(header_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # APPLICATION INFORMATION
            application_data = mortgage_info.get('Application', {})
            if application_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Application Information", self.styles['SubSectionHeader']))
                
                app_table_data = [["Application Detail", "Value"]]
                
                key_app_fields = [
                    ('MortgageProvider', 'Mortgage Provider'),
                    ('ApplicationDate', 'Application Date'),
                    ('LoanPurpose', 'Loan Purpose'),
                    ('OccupancyType', 'Occupancy Type'),
                    ('ApplicationChannel', 'Application Channel')
                ]
                
                for field, label in key_app_fields:
                    value = application_data.get(field)
                    if value:
                        app_table_data.append([label, self._format_value(value)])
                
                # Property valuation
                prop_valuation = application_data.get('ApplicationPropertyValuation')
                if isinstance(prop_valuation, (int, float)):
                    app_table_data.append(["Application Property Valuation", self._format_currency(prop_valuation)])
                
                # Denial reason if applicable
                denial_reason = application_data.get('DenialReason')
                if denial_reason and denial_reason != 'Not specified':
                    app_table_data.append(["Denial Reason", denial_reason])
                
                app_table = Table(app_table_data, colWidths=self.table_widths['two_col'])
                app_table.setStyle(self.table_styles['standard'])
                elements.append(app_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # BASIC FINANCIAL TERMS
            financial_data = mortgage_info.get('FinancialTerms', {})
            if financial_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Key Financial Terms", self.styles['SubSectionHeader']))
                
                financial_table_data = [["Financial Term", "Value"]]
                
                # Core financial metrics
                purchase_value = financial_data.get('PurchaseValue')
                if isinstance(purchase_value, (int, float)):
                    financial_table_data.append(["Purchase Value", self._format_currency(purchase_value)])
                
                original_loan = financial_data.get('OriginalLoan')
                if isinstance(original_loan, (int, float)):
                    financial_table_data.append(["Original Loan Amount", self._format_currency(original_loan)])
                
                original_term = financial_data.get('OriginalTerm')
                if isinstance(original_term, (int, float)):
                    years = original_term / 12
                    financial_table_data.append(["Original Term", f"{original_term} months ({years:.1f} years)"])
                
                original_rate = financial_data.get('OriginalLendingRate')
                if isinstance(original_rate, (int, float)):
                    financial_table_data.append(["Original Interest Rate", self._format_percentage(original_rate)])
                
                # LTV calculation
                if isinstance(purchase_value, (int, float)) and isinstance(original_loan, (int, float)) and purchase_value > 0:
                    ltv = (original_loan / purchase_value) * 100
                    financial_table_data.append(["Original LTV Ratio", f"{ltv:.1f}%"])
                
                financial_table = Table(financial_table_data, colWidths=self.table_widths['two_col'])
                financial_table.setStyle(self.table_styles['financial'])
                elements.append(financial_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MORTGAGE FEATURES
            features_data = mortgage_info.get('Features', {})
            if features_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Mortgage Features", self.styles['SubSectionHeader']))
                
                features_table_data = [["Feature", "Details"]]
                
                # Core features
                core_features = [
                    ('MortgageType', 'Mortgage Type'),
                    ('PaymentFrequency', 'Payment Frequency'),
                    ('RepaymentType', 'Repayment Type')
                ]
                
                for field, label in core_features:
                    value = features_data.get(field)
                    if value:
                        features_table_data.append([label, self._format_value(value)])
                
                # Key boolean features
                boolean_features = [
                    ('FirstTimeBuyerFlag', 'First Time Buyer'),
                    ('PaymentHolidayEligible', 'Payment Holiday Eligible'),
                    ('PortabilityFlag', 'Portability Available'),
                    ('OffsetAccount', 'Offset Account')
                ]
                
                for field, label in boolean_features:
                    value = features_data.get(field)
                    if value is not None:
                        features_table_data.append([label, self._format_value(value)])
                
                features_table = Table(features_table_data, colWidths=self.table_widths['two_col'])
                features_table.setStyle(self.table_styles['standard'])
                elements.append(features_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating mortgage overview: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements