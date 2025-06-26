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

# src/utilities/page_10_transactions.py

"""
Page 10: Transaction History
Handles sales history, rental information, and market activity.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class TransactionsPage(BasePage):
    """Generates transaction history page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate transaction history page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Transaction History", self.styles['SectionHeader']))
            
            transaction_data = property_data.get('TransactionHistory', {})
            
            if not transaction_data:
                elements.append(Paragraph("No transaction history available.", self.styles['Normal']))
                return elements
            
            # SALES HISTORY
            sales = transaction_data.get('Sales', {})
            if sales:
                elements.append(Paragraph("Sales Information", self.styles['SubSectionHeader']))
                
                sales_data = [["Sales Detail", "Information"]]
                
                # Sale price
                sale_price = sales.get('SalePriceGbp')
                if isinstance(sale_price, (int, float)):
                    sales_data.append(["Sale Price", self._format_currency(sale_price)])
                
                # Sale date
                sale_date = sales.get('SaleDate')
                if sale_date:
                    sales_data.append(["Sale Date", sale_date])
                
                # Previous owner
                previous_owner = sales.get('PreviousOwner')
                if previous_owner:
                    sales_data.append(["Previous Owner", previous_owner])
                
                # Marketing period
                marketing_days = sales.get('MarketingDays')
                if isinstance(marketing_days, (int, float)):
                    sales_data.append(["Marketing Period", f"{int(marketing_days)} days"])
                    
                    # Marketing assessment
                    if marketing_days < 30:
                        marketing_assessment = "Quick sale - High demand or competitive pricing"
                    elif marketing_days < 90:
                        marketing_assessment = "Normal marketing period"
                    elif marketing_days < 180:
                        marketing_assessment = "Extended marketing - May indicate pricing issues"
                    else:
                        marketing_assessment = "Very long marketing period - Possible market challenges"
                    
                    sales_data.append(["Marketing Assessment", marketing_assessment])
                
                # Add other sales fields
                for key, value in sales.items():
                    if key not in ['SalePriceGbp', 'SaleDate', 'PreviousOwner', 'MarketingDays'] and value is not None:
                        sales_data.append([self._format_field_name(key), self._format_value(value)])
                
                sales_table = Table(sales_data, colWidths=self.table_widths['two_col'])
                sales_table.setStyle(self.table_styles['financial'])
                elements.append(sales_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RENTAL HISTORY
            rental = transaction_data.get('Rental', {})
            if rental:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Rental Information", self.styles['SubSectionHeader']))
                
                rental_data = [["Rental Detail", "Information"]]
                
                # Monthly and annual rent
                monthly_rent = rental.get('MonthlyRentGbp')
                if isinstance(monthly_rent, (int, float)):
                    annual_rent = monthly_rent * 12
                    rental_data.append(["Monthly Rent", self._format_currency(monthly_rent)])
                    rental_data.append(["Annual Rent", self._format_currency(annual_rent)])
                
                # Rental history status
                rental_history = rental.get('RentalHistory')
                if rental_history:
                    rental_data.append(["Rental History", rental_history])
                
                # Vacancy information
                vacancy_count = rental.get('VacancyCount')
                if isinstance(vacancy_count, (int, float)):
                    rental_data.append(["Vacancy Periods", str(int(vacancy_count))])
                
                # Tenancy duration
                tenancy_duration = rental.get('TenancyDuration')
                if tenancy_duration:
                    rental_data.append(["Typical Tenancy Duration", tenancy_duration])
                
                # Add other rental fields
                for key, value in rental.items():
                    if key not in ['MonthlyRentGbp', 'RentalHistory', 'VacancyCount', 'TenancyDuration'] and value is not None:
                        rental_data.append([self._format_field_name(key), self._format_value(value)])
                
                rental_table = Table(rental_data, colWidths=self.table_widths['two_col'])
                rental_table.setStyle(self.table_styles['financial'])
                elements.append(rental_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MARKET ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Market Analysis", self.styles['SubSectionHeader']))
            
            market_analysis = self._perform_market_analysis(transaction_data, property_data)
            
            analysis_data = [["Analysis Factor", "Assessment"]]
            for factor, assessment in market_analysis.items():
                analysis_data.append([factor, assessment])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating transaction history: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _perform_market_analysis(self, transaction_data: Dict[str, Any], property_data: Dict[str, Any]) -> Dict[str, str]:
        """Perform market analysis based on transaction data."""
        analysis = {}
        
        sales = transaction_data.get('Sales', {})
        rental = transaction_data.get('Rental', {})
        
        # Investment yield analysis
        monthly_rent = rental.get('MonthlyRentGbp')
        sale_price = sales.get('SalePriceGbp')
        
        if isinstance(monthly_rent, (int, float)) and isinstance(sale_price, (int, float)) and sale_price > 0:
            annual_rent = monthly_rent * 12
            gross_yield = (annual_rent / sale_price) * 100
            analysis["Gross Rental Yield"] = f"{gross_yield:.2f}% - " + self._assess_yield(gross_yield)
        
        # Price analysis
        current_value = property_data.get('PropertyHeader', {}).get('Valuation', {}).get('PropertyValue')
        if isinstance(sale_price, (int, float)) and isinstance(current_value, (int, float)):
            appreciation = current_value - sale_price
            appreciation_pct = (appreciation / sale_price) * 100 if sale_price > 0 else 0
            analysis["Capital Appreciation"] = f"{appreciation_pct:.1f}% since last sale"
        
        # Marketing efficiency
        marketing_days = sales.get('MarketingDays')
        if isinstance(marketing_days, (int, float)):
            if marketing_days < 30:
                efficiency = "High - Quick sale indicates strong demand"
            elif marketing_days < 90:
                efficiency = "Good - Normal marketing period"
            else:
                efficiency = "Below average - Extended marketing period"
            analysis["Marketing Efficiency"] = efficiency
        
        # Rental stability
        rental_history = rental.get('RentalHistory', '').lower()
        vacancy_count = rental.get('VacancyCount', 0)
        
        if 'never rented' in rental_history:
            analysis["Rental History"] = "No rental history - Owner occupied property"
        elif isinstance(vacancy_count, (int, float)):
            if vacancy_count == 0:
                analysis["Rental Stability"] = "Excellent - No vacancy periods"
            elif vacancy_count <= 2:
                analysis["Rental Stability"] = "Good - Minimal vacancy"
            else:
                analysis["Rental Stability"] = "Concerning - Multiple vacancy periods"
        
        return analysis
    
    def _assess_yield(self, yield_pct: float) -> str:
        """Assess rental yield performance."""
        if yield_pct > 8:
            return "Excellent yield"
        elif yield_pct > 6:
            return "Good yield"
        elif yield_pct > 4:
            return "Average yield"
        elif yield_pct > 2:
            return "Below average yield"
        else:
            return "Poor yield"