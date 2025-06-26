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

# src/utilities/page_13_risk_analysis.py

"""
Page 13: Comprehensive Risk Analysis
Combines property and mortgage risks for overall assessment.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class RiskAnalysisPage(BasePage):
    """Generates comprehensive risk analysis page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate comprehensive risk analysis page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Comprehensive Risk Analysis", self.styles['SectionHeader']))
            
            if mortgage_data:
                # Combined property and mortgage risk analysis
                risk_assessment = self._comprehensive_risk_assessment(property_data, mortgage_data)
            else:
                # Property-only risk analysis
                risk_assessment = self._property_risk_assessment(property_data)
            
            # OVERALL RISK SUMMARY
            elements.append(Paragraph("Overall Risk Summary", self.styles['SubSectionHeader']))
            
            summary_data = [["Risk Category", "Score", "Weight", "Impact"]]
            
            total_weighted_score = 0
            total_weight = 0
            
            for category, details in risk_assessment['categories'].items():
                score = details['score']
                weight = details['weight']
                impact = details['impact']
                
                total_weighted_score += score * weight
                total_weight += weight
                
                summary_data.append([category, f"{score}/5", f"{weight}%", impact])
            
            # Calculate overall score
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
            overall_percentage = (overall_score / 5) * 100
            
            # Add summary rows
            summary_data.append(["", "", "", ""])
            summary_data.append(["OVERALL SCORE", f"{overall_score:.2f}/5.0", "100%", f"{overall_percentage:.1f}%"])
            summary_data.append(["RISK LEVEL", risk_assessment['overall_level'], "", risk_assessment['overall_color']])
            
            summary_table = Table(summary_data, colWidths=self.table_widths['risk_table'])
            summary_table.setStyle(self.table_styles['risk'])
            elements.append(summary_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # KEY RISK FACTORS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Key Risk Factors", self.styles['SubSectionHeader']))
            
            factors_data = [["Risk Factor", "Assessment"]]
            for factor, assessment in risk_assessment['key_factors'].items():
                factors_data.append([factor, assessment])
            
            factors_table = Table(factors_data, colWidths=self.table_widths['two_col'])
            factors_table.setStyle(self.table_styles['standard'])
            elements.append(factors_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # RECOMMENDATIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Risk Management Recommendations", self.styles['SubSectionHeader']))
            
            recommendations_data = [["Priority", "Recommended Action"]]
            for i, recommendation in enumerate(risk_assessment['recommendations'], 1):
                recommendations_data.append([f"Priority {i}", recommendation])
            
            recommendations_table = Table(recommendations_data, colWidths=self.table_widths['two_col'])
            recommendations_table.setStyle(self.table_styles['standard'])
            elements.append(recommendations_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MONITORING SCHEDULE
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Recommended Monitoring Schedule", self.styles['SubSectionHeader']))
            
            monitoring_data = [["Monitoring Item", "Frequency"]]
            for item, frequency in risk_assessment['monitoring'].items():
                monitoring_data.append([item, frequency])
            
            monitoring_table = Table(monitoring_data, colWidths=self.table_widths['two_col'])
            monitoring_table.setStyle(self.table_styles['standard'])
            elements.append(monitoring_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk analysis: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _comprehensive_risk_assessment(self, property_data: Dict[str, Any], 
                                     mortgage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment with both property and mortgage data."""
        
        # Extract key data
        mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
        property_flood_risk = (property_data.get('PropertyHeader', {})
                             .get('RiskAssessment', {})
                             .get('OverallFloodRisk', 'Unknown'))
        
        current_status = mortgage_info.get('CurrentStatus', {})
        borrower_details = mortgage_info.get('BorrowerDetails', {})
        
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
        key_factors = self._identify_key_factors(categories)
        recommendations = self._generate_recommendations(categories, overall_score)
        monitoring = self._generate_monitoring_schedule(overall_score)
        
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
    
    def _property_risk_assessment(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def _identify_key_factors(self, categories: Dict[str, Dict]) -> Dict[str, str]:
        """Identify the highest risk factors."""
        key_factors = {}
        
        # Sort by risk score
        sorted_categories = sorted(categories.items(), key=lambda x: x[1]['score'], reverse=True)
        
        # Take top 3 highest risk categories
        for i, (category, details) in enumerate(sorted_categories[:3]):
            if details['score'] >= 4:
                key_factors[f"High Risk Factor {i+1}"] = f"{category}: {details['impact']}"
            elif details['score'] >= 3:
                key_factors[f"Medium Risk Factor {i+1}"] = f"{category}: {details['impact']}"
        
        return key_factors
    
    def _generate_recommendations(self, categories: Dict[str, Dict], overall_score: float) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []
        
        # High-level recommendations based on overall score
        if overall_score >= 4:
            recommendations.append("URGENT: Immediate comprehensive risk mitigation required")
        elif overall_score >= 3:
            recommendations.append("HIGH PRIORITY: Implement targeted risk reduction measures")
        elif overall_score >= 2:
            recommendations.append("MODERATE: Consider preventive risk management strategies")
        else:
            recommendations.append("LOW: Maintain current risk management practices")
        
        # Specific recommendations based on individual categories
        for category, details in categories.items():
            if details['score'] >= 4:
                if 'Flood' in category:
                    recommendations.append("Install comprehensive flood protection measures")
                elif 'Payment' in category:
                    recommendations.append("Address payment performance issues immediately")
                elif 'LTV' in category:
                    recommendations.append("Consider reducing loan-to-value ratio")
                elif 'Credit' in category:
                    recommendations.append("Work on improving credit profile")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _generate_monitoring_schedule(self, overall_score: float) -> Dict[str, str]:
        """Generate appropriate monitoring schedule based on risk level."""
        if overall_score >= 4:
            return {
                'Overall risk review': 'Monthly',
                'Payment performance': 'Weekly',
                'Property condition': 'Quarterly',
                'Market conditions': 'Monthly',
                'Insurance coverage': 'Quarterly'
            }
        elif overall_score >= 3:
            return {
                'Overall risk review': 'Quarterly',
                'Payment performance': 'Monthly',
                'Property condition': 'Semi-annually',
                'Market conditions': 'Quarterly',
                'Insurance coverage': 'Annually'
            }
        else:
            return {
                'Overall risk review': 'Annually',
                'Payment performance': 'Quarterly',
                'Property condition': 'Annually',
                'Market conditions': 'Semi-annually',
                'Insurance coverage': 'Annually'
            }