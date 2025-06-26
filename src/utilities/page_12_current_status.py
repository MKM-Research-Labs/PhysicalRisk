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

# src/utilities/page_12_current_status.py

"""
Page 12: Current Mortgage Status
Handles current mortgage performance, payments, and status metrics.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class CurrentStatusPage(BasePage):
    """Generates current mortgage status page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate current mortgage status page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Current Mortgage Status", self.styles['SectionHeader']))
            
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            current_status = mortgage_info.get('CurrentStatus', {})
            
            if not current_status:
                elements.append(Paragraph("No current status data available.", self.styles['Normal']))
                return elements
            
            # PAYMENT STATUS
            elements.append(Paragraph("Payment Status", self.styles['SubSectionHeader']))
            
            payment_data = [["Payment Metric", "Value"]]
            
            # Latest status
            latest_status = current_status.get('LatestStatus')
            if latest_status:
                payment_data.append(["Current Status", latest_status])
            
            # Outstanding balance
            outstanding = current_status.get('OutstandingBalance')
            if isinstance(outstanding, (int, float)):
                payment_data.append(["Outstanding Balance", self._format_currency(outstanding)])
            
            # Current payment
            current_payment = current_status.get('CurrentPayment')
            if isinstance(current_payment, (int, float)):
                payment_data.append(["Monthly Payment", self._format_currency(current_payment)])
            
            # Last payment date
            last_payment = current_status.get('LastPaymentDate')
            if last_payment:
                payment_data.append(["Last Payment Date", last_payment])
            
            # Payments made
            total_payments = current_status.get('TotalPayments')
            if isinstance(total_payments, (int, float)):
                payment_data.append(["Total Payments Made", str(int(total_payments))])
            
            payment_table = Table(payment_data, colWidths=self.table_widths['two_col'])
            payment_table.setStyle(self.table_styles['financial'])
            elements.append(payment_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CURRENT FINANCIAL POSITION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Current Financial Position", self.styles['SubSectionHeader']))
            
            position_data = [["Financial Metric", "Current Value"]]
            
            # Current LTV
            current_ltv = current_status.get('CurrentLTV')
            if isinstance(current_ltv, (int, float)):
                ltv_percentage = current_ltv * 100 if current_ltv <= 1 else current_ltv
                position_data.append(["Current LTV Ratio", f"{ltv_percentage:.1f}%"])
                
                # LTV risk assessment
                if ltv_percentage > 90:
                    ltv_risk = "High Risk - Low equity position"
                elif ltv_percentage > 80:
                    ltv_risk = "Medium-High Risk"
                elif ltv_percentage > 70:
                    ltv_risk = "Medium Risk"
                elif ltv_percentage > 60:
                    ltv_risk = "Low-Medium Risk"
                else:
                    ltv_risk = "Low Risk - Strong equity position"
                
                position_data.append(["LTV Risk Assessment", ltv_risk])
            
            # Current interest rate
            current_rate = current_status.get('CurrentLendingRate')
            if isinstance(current_rate, (int, float)):
                position_data.append(["Current Interest Rate", self._format_percentage(current_rate)])
            
            # Current BoE base rate
            current_boe = current_status.get('CurrentBoEBase')
            if isinstance(current_boe, (int, float)):
                position_data.append(["Current BoE Base", self._format_currency(current_boe)])
            
            # Principal and interest paid
            principal_paid = current_status.get('PrincipalPayed')
            if isinstance(principal_paid, (int, float)):
                position_data.append(["Principal Paid to Date", self._format_currency(principal_paid)])
            
            interest_paid = current_status.get('InterestPayed')
            if isinstance(interest_paid, (int, float)):
                position_data.append(["Interest Paid to Date", self._format_currency(interest_paid)])
            
            position_table = Table(position_data, colWidths=self.table_widths['two_col'])
            position_table.setStyle(self.table_styles['financial'])
            elements.append(position_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ARREARS AND PAYMENT ISSUES
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Payment Performance", self.styles['SubSectionHeader']))
            
            performance_data = [["Performance Metric", "Status"]]
            
            # Arrears status
            in_arrears = current_status.get('InArrearsFlag')
            if in_arrears is not None:
                arrears_status = "Yes - ATTENTION REQUIRED" if in_arrears else "No - Current"
                performance_data.append(["Currently in Arrears", arrears_status])
            
            # Missed payments
            missed_payments = current_status.get('MissedPayments12M')
            if isinstance(missed_payments, (int, float)):
                missed_count = int(missed_payments)
                performance_data.append(["Missed Payments (12M)", str(missed_count)])
                
                # Performance assessment
                if missed_count == 0:
                    performance_assessment = "Excellent - No missed payments"
                elif missed_count <= 2:
                    performance_assessment = "Good - Minimal issues"
                elif missed_count <= 4:
                    performance_assessment = "Concerning - Multiple missed payments"
                else:
                    performance_assessment = "Poor - Significant payment issues"
                
                performance_data.append(["Payment Performance", performance_assessment])
            
            # Highest arrears amount
            highest_arrears = current_status.get('HighestArrearsLast24M')
            if isinstance(highest_arrears, (int, float)):
                performance_data.append(["Highest Arrears (24M)", self._format_currency(highest_arrears)])
            
            # Current arrears balance
            arrears_balance = current_status.get('ArrearsHighestBalance')
            if isinstance(arrears_balance, (int, float)):
                performance_data.append(["Arrears Balance", self._format_currency(arrears_balance)])
            
            performance_table = Table(performance_data, colWidths=self.table_widths['two_col'])
            performance_table.setStyle(self.table_styles['risk'])
            elements.append(performance_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PAYMENT HOLIDAYS
            payment_holidays_taken = current_status.get('PaymentHolidaysTaken')
            total_holidays = current_status.get('TotalPaymentHolidays')
            last_holiday = current_status.get('LastPaymentHolidayDate')
            
            if any([payment_holidays_taken, total_holidays, last_holiday]):
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Payment Holiday History", self.styles['SubSectionHeader']))
                
                holiday_data = [["Holiday Information", "Details"]]
                
                if isinstance(payment_holidays_taken, (int, float)):
                    holiday_data.append(["Payment Holidays Taken", str(int(payment_holidays_taken))])
                
                if isinstance(total_holidays, (int, float)):
                    holiday_data.append(["Total Payment Holidays", str(int(total_holidays))])
                
                if last_holiday:
                    holiday_data.append(["Last Payment Holiday", last_holiday])
                
                holiday_table = Table(holiday_data, colWidths=self.table_widths['two_col'])
                holiday_table.setStyle(self.table_styles['standard'])
                elements.append(holiday_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating current status: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements