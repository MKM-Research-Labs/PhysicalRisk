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

# src/utilities/page_06_financial.py

"""
Page 6: Financial Information
Handles property valuation, financial metrics, and investment analysis.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class FinancialPage(BasePage):
    """Generates financial information page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate financial information page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Financial Information", self.styles['SectionHeader']))
            
            header_data = property_data.get('PropertyHeader', {})
            valuation_data = header_data.get('Valuation', {})
            
            # PROPERTY VALUATION
            elements.append(Paragraph("Property Valuation", self.styles['SubSectionHeader']))
            
            valuation_table_data = [["Valuation Item", "Value"]]
            
            # Current property value
            property_value = valuation_data.get('PropertyValue')
            if isinstance(property_value, (int, float)):
                valuation_table_data.append(["Current Property Value", self._format_currency(property_value)])
                
                # Value per sqm if area is available
                attributes_data = header_data.get('PropertyAttributes', {})
                area = attributes_data.get('PropertyAreaSqm')
                if isinstance(area, (int, float)) and area > 0:
                    value_per_sqm = property_value / area
                    valuation_table_data.append(["Value per sqm", self._format_currency(value_per_sqm)])
            
            # Add other valuation fields
            for key, value in valuation_data.items():
                if key != 'PropertyValue' and value is not None:
                    if isinstance(value, (int, float)) and 'value' in key.lower():
                        valuation_table_data.append([self._format_field_name(key), self._format_currency(value)])
                    else:
                        valuation_table_data.append([self._format_field_name(key), self._format_value(value)])
            
            valuation_table = Table(valuation_table_data, colWidths=self.table_widths['two_col'])
            valuation_table.setStyle(self.table_styles['financial'])
            elements.append(valuation_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # TRANSACTION HISTORY FINANCIAL SUMMARY
            transaction_data = property_data.get('TransactionHistory', {})
            
            if transaction_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Transaction Financial Summary", self.styles['SubSectionHeader']))
                
                transaction_table_data = [["Transaction Type", "Financial Details"]]
                
                # Sales information
                sales_data = transaction_data.get('Sales', {})
                if sales_data:
                    sale_price = sales_data.get('SalePriceGbp')
                    if isinstance(sale_price, (int, float)):
                        transaction_table_data.append(["Last Sale Price", self._format_currency(sale_price)])
                        
                        # Calculate appreciation if current value available
                        if isinstance(property_value, (int, float)):
                            appreciation = property_value - sale_price
                            appreciation_pct = (appreciation / sale_price) * 100 if sale_price > 0 else 0
                            transaction_table_data.append(["Value Appreciation", self._format_currency(appreciation)])
                            transaction_table_data.append(["Appreciation %", f"{appreciation_pct:.1f}%"])
                    
                    sale_date = sales_data.get('SaleDate')
                    if sale_date:
                        transaction_table_data.append(["Sale Date", sale_date])
                
                # Rental information
                rental_data = transaction_data.get('Rental', {})
                if rental_data:
                    monthly_rent = rental_data.get('MonthlyRentGbp')
                    if isinstance(monthly_rent, (int, float)):
                        annual_rent = monthly_rent * 12
                        transaction_table_data.append(["Monthly Rent", self._format_currency(monthly_rent)])
                        transaction_table_data.append(["Annual Rent", self._format_currency(annual_rent)])
                        
                        # Calculate rental yield if property value available
                        if isinstance(property_value, (int, float)) and property_value > 0:
                            rental_yield = (annual_rent / property_value) * 100
                            transaction_table_data.append(["Gross Rental Yield", f"{rental_yield:.2f}%"])
                
                transaction_table = Table(transaction_table_data, colWidths=self.table_widths['two_col'])
                transaction_table.setStyle(self.table_styles['financial'])
                elements.append(transaction_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FINANCIAL ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Financial Analysis", self.styles['SubSectionHeader']))
            
            analysis_data = [["Analysis Factor", "Assessment"]]
            
            # Market position analysis
            if isinstance(property_value, (int, float)):
                if property_value > 1000000:
                    market_segment = "Premium market segment"
                elif property_value > 500000:
                    market_segment = "Upper-middle market segment"
                elif property_value > 250000:
                    market_segment = "Middle market segment"
                else:
                    market_segment = "Entry-level market segment"
                
                analysis_data.append(["Market Segment", market_segment])
            
            # Investment potential
            rental_data = transaction_data.get('Rental', {}) if transaction_data else {}
            monthly_rent = rental_data.get('MonthlyRentGbp')
            
            if isinstance(property_value, (int, float)) and isinstance(monthly_rent, (int, float)):
                annual_rent = monthly_rent * 12
                rental_yield = (annual_rent / property_value) * 100
                
                if rental_yield > 8:
                    investment_rating = "Excellent - High yield potential"
                elif rental_yield > 6:
                    investment_rating = "Good - Above average yield"
                elif rental_yield > 4:
                    investment_rating = "Fair - Average yield"
                elif rental_yield > 2:
                    investment_rating = "Below average yield"
                else:
                    investment_rating = "Poor yield potential"
                
                analysis_data.append(["Investment Rating", investment_rating])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating financial information: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements