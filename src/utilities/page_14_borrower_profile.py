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

# src/utilities/page_14_borrower_profile.py

"""
Page 14: Borrower Profile
Handles borrower demographics, employment, and financial profile.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class BorrowerProfilePage(BasePage):
    """Generates borrower profile page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate borrower profile page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage/borrower data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Borrower Profile", self.styles['SectionHeader']))
            
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            borrower_details = mortgage_info.get('BorrowerDetails', {})
            
            if not borrower_details:
                elements.append(Paragraph("No borrower details available.", self.styles['Normal']))
                return elements
            
            # PERSONAL INFORMATION
            elements.append(Paragraph("Personal Information", self.styles['SubSectionHeader']))
            
            personal_data = [["Personal Detail", "Information"]]
            
            # Demographics
            age = borrower_details.get('BorrowerAge')
            if isinstance(age, (int, float)):
                personal_data.append(["Age", f"{int(age)} years"])
            
            marital_status = borrower_details.get('MaritalStatus')
            if marital_status:
                personal_data.append(["Marital Status", marital_status])
            
            family_members = borrower_details.get('FamilyMembers')
            if isinstance(family_members, (int, float)):
                personal_data.append(["Family Members", str(int(family_members))])
            
            nationality = borrower_details.get('BorrowerNationality')
            if nationality:
                personal_data.append(["Nationality", nationality])
            
            residency_status = borrower_details.get('ResidencyStatus')
            if residency_status:
                personal_data.append(["Residency Status", residency_status])
            
            personal_table = Table(personal_data, colWidths=self.table_widths['two_col'])
            personal_table.setStyle(self.table_styles['standard'])
            elements.append(personal_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # EMPLOYMENT & INCOME
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Employment & Income", self.styles['SubSectionHeader']))
            
            employment_data = [["Employment Detail", "Information"]]
            
            # Employment status
            employment = borrower_details.get('BorrowerEmployment')
            if employment:
                employment_data.append(["Employment Status", employment])
            
            # Years in current employment
            years_employed = borrower_details.get('YearsInCurrentEmployment')
            if isinstance(years_employed, (int, float)):
                employment_data.append(["Years in Current Employment", f"{int(years_employed)} years"])
                
                # Employment stability assessment
                if years_employed >= 5:
                    stability = "Excellent - Long-term stability"
                elif years_employed >= 2:
                    stability = "Good - Established employment"
                elif years_employed >= 1:
                    stability = "Fair - Recent employment"
                else:
                    stability = "Concerning - Very recent employment"
                
                employment_data.append(["Employment Stability", stability])
            
            # Income verification
            income_verification = borrower_details.get('IncomeVerificationType')
            if income_verification:
                employment_data.append(["Income Verification Type", income_verification])
            
            employment_table = Table(employment_data, colWidths=self.table_widths['two_col'])
            employment_table.setStyle(self.table_styles['standard'])
            elements.append(employment_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # INCOME ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Income Analysis", self.styles['SubSectionHeader']))
            
            income_data = [["Income Component", "Annual Amount"]]
            
            # Primary income
            primary_income = borrower_details.get('BorrowerIncome')
            if isinstance(primary_income, (int, float)):
                income_data.append(["Primary Income", self._format_currency(primary_income)])
                monthly_income = primary_income / 12
                income_data.append(["Monthly Income", self._format_currency(monthly_income)])
            
            # Secondary income
            secondary_income = borrower_details.get('SecondaryIncome')
            if isinstance(secondary_income, (int, float)):
                income_data.append(["Secondary Income", self._format_currency(secondary_income)])
            
            # Total income calculation
            if isinstance(primary_income, (int, float)):
                total_income = primary_income
                if isinstance(secondary_income, (int, float)):
                    total_income += secondary_income
                
                income_data.append(["Total Annual Income", self._format_currency(total_income)])
                
                # Income adequacy assessment
                if total_income >= 100000:
                    adequacy = "High - Strong income level"
                elif total_income >= 50000:
                    adequacy = "Good - Adequate income level"
                elif total_income >= 30000:
                    adequacy = "Fair - Moderate income level"
                else:
                    adequacy = "Limited - Lower income level"
                
                income_data.append(["Income Adequacy", adequacy])
            
            income_table = Table(income_data, colWidths=self.table_widths['two_col'])
            income_table.setStyle(self.table_styles['financial'])
            elements.append(income_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CREDITWORTHINESS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Creditworthiness Assessment", self.styles['SubSectionHeader']))
            
            credit_data = [["Credit Factor", "Assessment"]]
            
            # Credit score
            credit_score = borrower_details.get('BorrowerCreditScore')
            if isinstance(credit_score, (int, float)):
                credit_data.append(["Credit Score", str(int(credit_score))])
                
                # Credit score interpretation
                if credit_score >= 800:
                    credit_rating = "Excellent (800+)"
                    credit_description = "Exceptional credit profile"
                elif credit_score >= 740:
                    credit_rating = "Very Good (740-799)"
                    credit_description = "Strong credit profile"
                elif credit_score >= 670:
                    credit_rating = "Good (670-739)"
                    credit_description = "Good credit profile"
                elif credit_score >= 580:
                    credit_rating = "Fair (580-669)"
                    credit_description = "Fair credit with some concerns"
                else:
                    credit_rating = "Poor (<580)"
                    credit_description = "Poor credit requiring attention"
                
                credit_data.append(["Credit Rating", credit_rating])
                credit_data.append(["Credit Assessment", credit_description])
            
            credit_table = Table(credit_data, colWidths=self.table_widths['two_col'])
            credit_table.setStyle(self.table_styles['standard'])
            elements.append(credit_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # BORROWER RISK PROFILE
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Borrower Risk Profile", self.styles['SubSectionHeader']))
            
            risk_profile = self._assess_borrower_risk(borrower_details)
            
            profile_data = [["Risk Factor", "Assessment"]]
            for factor, assessment in risk_profile.items():
                profile_data.append([factor, assessment])
            
            profile_table = Table(profile_data, colWidths=self.table_widths['two_col'])
            profile_table.setStyle(self.table_styles['risk'])
            elements.append(profile_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating borrower profile: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _assess_borrower_risk(self, borrower_details: Dict[str, Any]) -> Dict[str, str]:
        """Assess overall borrower risk profile."""
        risk_profile = {}
        
        # Credit risk
        credit_score = borrower_details.get('BorrowerCreditScore')
        if isinstance(credit_score, (int, float)):
            if credit_score >= 740:
                risk_profile["Credit Risk"] = "Low - Excellent credit history"
            elif credit_score >= 670:
                risk_profile["Credit Risk"] = "Low-Medium - Good credit history"
            elif credit_score >= 580:
                risk_profile["Credit Risk"] = "Medium - Fair credit history"
            else:
                risk_profile["Credit Risk"] = "High - Poor credit history"
        
        # Employment stability risk
        years_employed = borrower_details.get('YearsInCurrentEmployment')
        if isinstance(years_employed, (int, float)):
            if years_employed >= 5:
                risk_profile["Employment Risk"] = "Low - Stable long-term employment"
            elif years_employed >= 2:
                risk_profile["Employment Risk"] = "Low-Medium - Established employment"
            else:
                risk_profile["Employment Risk"] = "Medium-High - Recent employment changes"
        
        # Income adequacy risk
        income = borrower_details.get('BorrowerIncome')
        if isinstance(income, (int, float)):
            if income >= 100000:
                risk_profile["Income Risk"] = "Low - High income level"
            elif income >= 50000:
                risk_profile["Income Risk"] = "Low-Medium - Adequate income"
            else:
                risk_profile["Income Risk"] = "Medium - Limited income level"
        
        # Age-related risk
        age = borrower_details.get('BorrowerAge')
        if isinstance(age, (int, float)):
            if 25 <= age <= 55:
                risk_profile["Age Risk"] = "Low - Prime earning years"
            elif age < 25:
                risk_profile["Age Risk"] = "Medium - Early career stage"
            else:
                risk_profile["Age Risk"] = "Medium - Approaching retirement"
        
        return risk_profile