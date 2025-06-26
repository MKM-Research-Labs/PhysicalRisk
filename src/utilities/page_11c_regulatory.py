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

# src/utilities/page_11c_regulatory.py

"""
Page 11c: Regulatory Compliance
Comprehensive regulatory information including MCOB, HMDA, and general compliance.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class RegulatoryPage(BasePage):
    """Generates regulatory compliance page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate regulatory compliance page elements."""
        elements = []
        
        if not mortgage_data:
            elements.append(Paragraph("No mortgage data available.", self.styles['Normal']))
            return elements
        
        try:
            elements.append(Paragraph("Regulatory Compliance", self.styles['SectionHeader']))
            
            mortgage_info = mortgage_data.get('Mortgage', mortgage_data)
            regulatory_data = mortgage_info.get('Regulatory', {})
            
            if not regulatory_data:
                elements.append(Paragraph("No regulatory information available.", self.styles['Normal']))
                return elements
            
            # GENERAL REGULATORY COMPLIANCE
            common_reg = regulatory_data.get('Common', {})
            if common_reg:
                elements.append(Paragraph("General Regulatory Information", self.styles['SubSectionHeader']))
                
                common_data = [["Regulatory Item", "Status"]]
                
                # FCA information
                fca_ref = common_reg.get('FCAReferenceNumber')
                if fca_ref:
                    common_data.append(["FCA Reference Number", fca_ref])
                
                # Business purpose
                business_purpose = common_reg.get('BusinessOrCommercialPurpose')
                if business_purpose is not None:
                    common_data.append(["Business/Commercial Purpose", self._format_value(business_purpose)])
                
                # Advice and execution flags
                regulatory_flags = [
                    ('AdvisedFlag', 'Advised Transaction'),
                    ('ExecutionOnlyFlag', 'Execution Only'),
                    ('ExecutionOnlyEligibilityFlag', 'Execution Only Eligible'),
                    ('InteractiveSaleFlag', 'Interactive Sale'),
                    ('DistanceMarketingFlag', 'Distance Marketing'),
                    ('RecordKeepingCompliantFlag', 'Record Keeping Compliant'),
                    ('VulnerableCustomerFlag', 'Vulnerable Customer')
                ]
                
                for key, label in regulatory_flags:
                    value = common_reg.get(key)
                    if value is not None:
                        common_data.append([label, self._format_value(value)])
                
                common_table = Table(common_data, colWidths=self.table_widths['two_col'])
                common_table.setStyle(self.table_styles['standard'])
                elements.append(common_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MCOB COMPLIANCE
            mcob_data = regulatory_data.get('MCOB', {})
            if mcob_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("MCOB (Mortgage Conduct of Business) Compliance", self.styles['SubSectionHeader']))
                
                mcob_table_data = [["MCOB Requirement", "Value/Status"]]
                
                # MMR compliance
                mmr_compliant = mcob_data.get('MMRCompliantFlag')
                if mmr_compliant is not None:
                    mcob_table_data.append(["MMR Compliant", self._format_value(mmr_compliant)])
                
                # Cross-border information
                cross_border = mcob_data.get('CrossBorderPassportingFlag')
                if cross_border is not None:
                    mcob_table_data.append(["Cross Border Passporting", self._format_value(cross_border)])
                
                originating_state = mcob_data.get('OriginatingMemberState')
                if originating_state:
                    mcob_table_data.append(["Originating Member State", originating_state])
                
                # ESIS information
                esis_date = mcob_data.get('ESISProvidedDate')
                if esis_date:
                    mcob_table_data.append(["ESIS Provided Date", esis_date])
                
                esis_version = mcob_data.get('ESISVersion')
                if esis_version:
                    mcob_table_data.append(["ESIS Version", esis_version])
                
                # Cooling off period
                cooling_off = mcob_data.get('CoolingOffPeriodDays')
                if isinstance(cooling_off, (int, float)):
                    mcob_table_data.append(["Cooling Off Period", f"{int(cooling_off)} days"])
                
                # Foreign currency information
                foreign_currency = mcob_data.get('ForeignCurrencyLoanFlag')
                if foreign_currency is not None:
                    mcob_table_data.append(["Foreign Currency Loan", self._format_value(foreign_currency)])
                
                exchange_protection = mcob_data.get('ExchangeRateProtectionType')
                if exchange_protection:
                    mcob_table_data.append(["Exchange Rate Protection", exchange_protection])
                
                mcob_table = Table(mcob_table_data, colWidths=self.table_widths['two_col'])
                mcob_table.setStyle(self.table_styles['standard'])
                elements.append(mcob_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
                
                # MCOB ADVICE AND DISCLOSURE
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("MCOB Advice & Disclosure", self.styles['SubSectionHeader']))
                
                advice_data = [["Advice/Disclosure Item", "Details"]]
                
                # Advice rejection
                advice_rejection = mcob_data.get('AdviceRejectionFlag')
                if advice_rejection is not None:
                    advice_data.append(["Advice Rejected", self._format_value(advice_rejection)])
                
                advice_rejection_reason = mcob_data.get('AdviceRejectionReason')
                if advice_rejection_reason:
                    advice_data.append(["Advice Rejection Reason", advice_rejection_reason])
                
                # APRC rates
                aprc_initial = mcob_data.get('APRCInitialRate')
                if isinstance(aprc_initial, (int, float)):
                    advice_data.append(["APRC Initial Rate", self._format_percentage(aprc_initial)])
                
                aprc_secondary = mcob_data.get('APRCSecondaryRate')
                if isinstance(aprc_secondary, (int, float)):
                    advice_data.append(["APRC Secondary Rate", self._format_percentage(aprc_secondary)])
                
                # Stress test compliance
                stress_test = mcob_data.get('StressTestCompliantFlag')
                if stress_test is not None:
                    advice_data.append(["Stress Test Compliant", self._format_value(stress_test)])
                
                # Assessment dates
                affordability_date = mcob_data.get('AffordabilityAssessmentDate')
                if affordability_date:
                    advice_data.append(["Affordability Assessment Date", affordability_date])
                
                suitability_date = mcob_data.get('SuitabilityAssessmentDate')
                if suitability_date:
                    advice_data.append(["Suitability Assessment Date", suitability_date])
                
                # Disclosure information
                initial_disclosure_date = mcob_data.get('InitialDisclosureProvidedDate')
                if initial_disclosure_date:
                    advice_data.append(["Initial Disclosure Date", initial_disclosure_date])
                
                initial_disclosure_method = mcob_data.get('InitialDisclosureMethod')
                if initial_disclosure_method:
                    advice_data.append(["Initial Disclosure Method", initial_disclosure_method])
                
                # Cancellation rights
                cancellation_rights = mcob_data.get('CancellationRightsFlag')
                if cancellation_rights is not None:
                    advice_data.append(["Cancellation Rights", self._format_value(cancellation_rights)])
                
                # Professional codes
                mortgage_club_code = mcob_data.get('MortgageClubCode')
                if mortgage_club_code:
                    advice_data.append(["Mortgage Club Code", mortgage_club_code])
                
                intermediary_code = mcob_data.get('IntermediaryCode')
                if intermediary_code:
                    advice_data.append(["Intermediary Code", intermediary_code])
                
                # Advice retention
                advice_retention = mcob_data.get('AdviceRetentionPeriod')
                if isinstance(advice_retention, (int, float)):
                    advice_data.append(["Advice Retention Period", f"{int(advice_retention)} years"])
                
                advice_table = Table(advice_data, colWidths=self.table_widths['two_col'])
                advice_table.setStyle(self.table_styles['standard'])
                elements.append(advice_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # HMDA COMPLIANCE
            hmda_data = regulatory_data.get('HMDA', {})
            if hmda_data:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("HMDA Compliance", self.styles['SubSectionHeader']))
                
                hmda_table_data = [["HMDA Requirement", "Value/Status"]]
                
                # HMDA reportable status
                hmda_reportable = hmda_data.get('HMDAReportableFlag')
                if hmda_reportable is not None:
                    hmda_table_data.append(["HMDA Reportable", self._format_value(hmda_reportable)])
                
                # HOEPA status
                hoepa_status = hmda_data.get('HMDAHOEPAStatus')
                if hoepa_status is not None:
                    hmda_table_data.append(["HOEPA Status", self._format_value(hoepa_status)])
                
                # HMDA rate spread
                hmda_rate_spread = hmda_data.get('HMDARateSpread')
                if isinstance(hmda_rate_spread, (int, float)):
                    hmda_table_data.append(["HMDA Rate Spread", self._format_currency(hmda_rate_spread)])
                
                # Manufactured home information
                manufactured_secured = hmda_data.get('ManufacturedHomeSecured')
                if manufactured_secured is not None:
                    hmda_table_data.append(["Manufactured Home Secured", self._format_value(manufactured_secured)])
                
                manufactured_interest = hmda_data.get('ManufacturedHomeLandPropertyInterest')
                if manufactured_interest:
                    hmda_table_data.append(["Manufactured Home Land Interest", manufactured_interest])
                
                hmda_table = Table(hmda_table_data, colWidths=self.table_widths['two_col'])
                hmda_table.setStyle(self.table_styles['standard'])
                elements.append(hmda_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating regulatory compliance information: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements