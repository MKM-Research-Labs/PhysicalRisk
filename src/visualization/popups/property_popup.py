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
Property popup creation functionality.

This module handles the creation of detailed popups for property markers,
including property information, mortgage details, flood risk analysis,
and mortgage risk assessment.
"""

from typing import Dict, Any, Optional
import folium
from .popup_builder import PopupBuilder


class PropertyPopupBuilder(PopupBuilder):
    """Builder for property information popups."""
    
    def __init__(self):
        """Initialize the property popup builder."""
        super().__init__()
    
    def create_property_section(self, prop: Dict[str, Any], property_id: str, 
                              address: Dict[str, Any], coordinates: str, 
                              construction_year: Any, property_age_factor: str, 
                              property_value: Any, has_mortgage: bool) -> str:
        """
        Create the property information section for the popup.
        
        Args:
            prop: Property data dictionary
            property_id: Property ID
            address: Address dictionary
            coordinates: Formatted coordinates string
            construction_year: Year of construction
            property_age_factor: Property age risk factor
            property_value: Property value
            has_mortgage: Boolean indicating if property has a mortgage
            
        Returns:
            HTML string for the property information section
        """
        # Format the address
        formatted_address = f"{address.get('building_number', '')} {address.get('street_name', '')}, {address.get('town_city', '')}"
        if address.get('post_code'):
            formatted_address += f", {address['post_code']}"
        
        # Format property value
        value_display = self.format_currency(property_value)
        
        # Get property header data safely
        prop_header = prop.get('PropertyHeader', {})
        header = prop_header.get('Header', {})
        attributes = prop_header.get('PropertyAttributes', {})
        construction = prop_header.get('Construction', {})
        
        content = f"""
            {self.create_data_row("Property Type", header.get('propertyType', 'Unknown'))}
            {self.create_data_row("Status", header.get('propertyStatus', 'Unknown'))}
            {self.create_data_row("Building Type", attributes.get('PropertyType', 'Unknown'))}
            {self.create_data_row("Address", formatted_address)}
            {self.create_data_row("Coordinates", coordinates)}
            {self.create_data_row("Construction Year", f"{construction_year} ({property_age_factor})")}
            {self.create_data_row("Number of Storeys", attributes.get('NumberOfStoreys', 'Unknown'))}
            {self.create_data_row("Construction Type", construction.get('ConstructionType', 'Unknown'))}
            {self.create_data_row("Property Value", value_display)}
        """
        
        return self.create_section("Property Information", content)
    
    def create_flood_info_section(self, flood_info: Dict[str, Any]) -> str:
        """
        Create the flood risk information section for the popup.
        
        Args:
            flood_info: Dictionary containing flood risk information
            
        Returns:
            HTML string for the flood risk information section or empty string if no info
        """
        if not flood_info:
            return ""
        
        risk_level = flood_info.get('risk_level', 'Unknown')
        risk_color = self.get_risk_color(risk_level)
        
        content = f"""
            {self.create_data_row("Nearest Gauge", flood_info.get('nearest_gauge', 'N/A'))}
            {self.create_data_row("Distance to Gauge", f"{self.safe_format_float(flood_info.get('distance_to_gauge', 'N/A'))} km")}
            {self.create_data_row("Water Level", f"{self.safe_format_float(flood_info.get('water_level', 'N/A'))} m")}
            {self.create_data_row("Flood Depth", f"{self.safe_format_float(flood_info.get('flood_depth', 'N/A'))} m")}
            {self.create_data_row("Risk Value", flood_info.get('risk_value', 'N/A'))}
            {self.create_data_row("Risk Level", self.create_colored_text(risk_level, risk_color, bold=True))}
            {self.create_data_row("Value at Risk", self.format_currency(flood_info.get('value_at_risk', 'N/A')))}
        """
        
        return self.create_section("Detailed Flood Risk Information", content, "#D5F5E3", "#1E8449")
    
    def create_mortgage_section(self, mortgage_info: Dict[str, Any], 
                              property_value: Any, flood_risk_level: str) -> str:
        """
        Create the mortgage information section for the popup.
        
        Args:
            mortgage_info: Dictionary containing mortgage information
            property_value: Property value
            flood_risk_level: Flood risk level string
            
        Returns:
            HTML string for the mortgage information section
        """
        # Extract mortgage data from different possible structures
        mortgage_header = mortgage_info.get('Header', {})
        mortgage_financial = mortgage_info.get('FinancialTerms', {})
        mortgage_application = mortgage_info.get('Application', {})
        
        # If mortgage info is nested differently, try to find the correct structure
        if not mortgage_header and 'Mortgage' in mortgage_info:
            mortgage_header = mortgage_info.get('Mortgage', {}).get('Header', {})
            mortgage_financial = mortgage_info.get('Mortgage', {}).get('FinancialTerms', {})
            mortgage_application = mortgage_info.get('Mortgage', {}).get('Application', {})
        
        mortgage_id = mortgage_header.get('MortgageID', 'N/A')
        lender = mortgage_application.get('MortgageProvider', 'N/A')
        
        # Financial terms
        loan_amount = mortgage_financial.get('OriginalLoan', 0)
        loan_amount_formatted = self.format_currency(loan_amount)
        
        interest_rate = mortgage_financial.get('OriginalLendingRate', 0)
        interest_rate_formatted = self.format_percentage(interest_rate)
        
        # Calculate LTV based on loan amount and property value
        ltv_ratio = self._calculate_ltv_ratio(loan_amount, property_value, mortgage_financial)
        ltv_formatted = self.format_percentage(ltv_ratio)
        
        # Get term years
        term_years = self._extract_term_years(mortgage_financial, mortgage_info)
        term_years_formatted = f"{term_years:.0f}" if isinstance(term_years, (int, float)) else 'N/A'
        
        # Calculate monthly payment
        monthly_payment = self._calculate_monthly_payment(
            mortgage_financial, loan_amount, interest_rate, term_years
        )
        monthly_payment_formatted = self.format_currency(monthly_payment)
        
        content = f"""
            {self.create_data_row("Mortgage ID", mortgage_id)}
            {self.create_data_row("Lender", lender)}
            {self.create_data_row("Loan Amount", loan_amount_formatted)}
            {self.create_data_row("Interest Rate", interest_rate_formatted)}
            {self.create_data_row("Term", f"{term_years_formatted} years")}
            {self.create_data_row("Monthly Payment", monthly_payment_formatted)}
            {self.create_data_row("LTV Ratio", ltv_formatted)}
        """
        
        # Create header with special styling
        header_html = """
        <div style="margin-top: 20px; border-top: 3px solid #8E44AD; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD; text-align: center; background-color: #E8DAEF; padding: 5px; border-radius: 5px;">MORTGAGE DETAILS</h4>
        """
        
        section_html = self.create_section("Loan Information", content, "#E8DAEF", "#6C3483")
        
        return header_html + section_html + "</div>"
    
    def create_mortgage_risk_section(self, mortgage_risk_info: Dict[str, Any]) -> str:
        """
        Create the mortgage risk analysis section for the popup.
        
        Args:
            mortgage_risk_info: Dictionary containing mortgage risk data
            
        Returns:
            HTML string for the mortgage risk section or empty string if no info
        """
        if not mortgage_risk_info:
            return ""
        
        # Format mortgage details
        loan_amount = mortgage_risk_info.get('loan_amount', 0)
        interest_rate = mortgage_risk_info.get('interest_rate', 0)
        monthly_payment = mortgage_risk_info.get('monthly_payment', 0)
        annual_payment = mortgage_risk_info.get('annual_payment', 0)
        credit_spread = mortgage_risk_info.get('credit_spread', 0)
        recovery_haircut = mortgage_risk_info.get('recovery_haircut', 0)
        mortgage_value = mortgage_risk_info.get('mortgage_value', 0)
        mortgage_value_at_risk = mortgage_risk_info.get('mortgage_value_at_risk', 0)
        flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
        flood_risk_value = mortgage_risk_info.get('flood_risk_value', 0)
        flood_depth = mortgage_risk_info.get('flood_depth', 0)
        property_value = mortgage_risk_info.get('property_value', 0)
        
        # Calculate LTV ratio
        ltv_ratio = 0
        if isinstance(loan_amount, (int, float)) and isinstance(property_value, (int, float)) and property_value > 0:
            ltv_ratio = loan_amount / property_value
        
        # Mortgage details section
        mortgage_details_content = f"""
            {self.create_data_row("Mortgage ID", mortgage_risk_info.get('MortgageID', 'N/A'))}
            {self.create_data_row("Loan Amount", self.format_currency(loan_amount))}
            {self.create_data_row("Interest Rate", self.format_percentage(interest_rate))}
            {self.create_data_row("Monthly Payment", self.format_currency(monthly_payment))}
            {self.create_data_row("Annual Payment", self.format_currency(annual_payment))}
            {self.create_data_row("Property Value", self.format_currency(property_value))}
            {self.create_data_row("LTV Ratio", self.format_percentage(ltv_ratio))}
        """
        
        # Risk metrics section
        risk_metrics_content = f"""
            {self.create_data_row("Credit Spread", self.format_percentage(credit_spread))}
            {self.create_data_row("Recovery Haircut", self.format_percentage(recovery_haircut))}
            {self.create_data_row("Mortgage Value", self.format_currency(mortgage_value))}
            {self.create_data_row("Mortgage Value at Risk", self.format_currency(mortgage_value_at_risk))}
            {self.create_data_row("Flood Risk Level", self.create_colored_text(flood_risk_level, self.get_risk_color(flood_risk_level), bold=True))}
            {self.create_data_row("Flood Risk Value", self.format_percentage(flood_risk_value))}
            {self.create_data_row("Flood Depth", f"{self.safe_format_float(flood_depth)} m")}
        """
        
        # Overall risk assessment
        risk_summary = self._get_mortgage_risk_summary(flood_risk_level, mortgage_value, loan_amount, ltv_ratio)
        risk_color = self._get_overall_risk_color(flood_risk_level, mortgage_value, loan_amount, ltv_ratio)
        
        impact_assessment_content = f"""
            {self.create_data_row("Overall Assessment", self.create_colored_text(risk_summary, risk_color, bold=True))}
        """
        
        # Build complete section
        header_html = """
        <div style="margin-top: 20px; border-top: 3px solid #5DADE2; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #2E86C1; text-align: center; background-color: #D6EAF8; padding: 5px; border-radius: 5px;">MORTGAGE RISK ANALYSIS</h4>
        """
        
        details_section = self.create_section("Mortgage Details", mortgage_details_content, "#D6EAF8", "#2874A6")
        risk_section = self.create_section("Risk Metrics", risk_metrics_content, "#FCF3CF", "#B7950B")
        impact_section = self.create_section("Impact Assessment", impact_assessment_content, "#FADBD8", "#943126")
        
        return header_html + details_section + risk_section + impact_section + "</div>"
    
    def _calculate_ltv_ratio(self, loan_amount: Any, property_value: Any, 
                           mortgage_financial: Dict[str, Any]) -> float:
        """Calculate LTV ratio from available data."""
        if isinstance(loan_amount, (int, float)) and property_value and isinstance(property_value, (int, float)) and property_value > 0:
            return loan_amount / property_value
        else:
            # Fallback to stored LTV if available
            return mortgage_financial.get('LoanToValueRatio', 0)
    
    def _extract_term_years(self, mortgage_financial: Dict[str, Any], 
                          mortgage_info: Dict[str, Any]) -> Optional[float]:
        """Extract term years from various possible fields."""
        # Try different field names for term years
        for field in ['TermYears', 'Term', 'LoanTerm', 'OriginalTerm']:
            if field in mortgage_financial:
                term_years = mortgage_financial.get(field)
                # If term is in months, convert to years
                if field == 'OriginalTerm' and term_years and term_years > 100:
                    return term_years / 12
                return term_years
        
        # Try other nested structures
        for path in [
            ['term_years'],
            ['Term', 'Years'],
            ['LoanTerms', 'Years']
        ]:
            current = mortgage_info
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    current = None
                    break
            if current is not None:
                return current
        
        return None
    
    def _calculate_monthly_payment(self, mortgage_financial: Dict[str, Any], 
                                 loan_amount: Any, interest_rate: Any, 
                                 term_years: Any) -> Optional[float]:
        """Calculate monthly payment from loan terms."""
        # First check if monthly payment is directly available
        for field in ['MonthlyPayment', 'Payment', 'RegularPayment']:
            if field in mortgage_financial:
                return mortgage_financial.get(field)
        
        # Calculate if we have the required data
        if (isinstance(loan_amount, (int, float)) and 
            isinstance(interest_rate, (int, float)) and 
            isinstance(term_years, (int, float))):
            
            monthly_rate = interest_rate / 100 / 12
            num_payments = term_years * 12
            
            if monthly_rate > 0 and num_payments > 0:
                try:
                    return loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
                except Exception:
                    pass
        
        return None
    
    def _get_mortgage_risk_summary(self, flood_risk_level: str, mortgage_value: float, 
                                 loan_amount: float, ltv_ratio: float) -> str:
        """Generate a summary assessment of mortgage risk."""
        # Check for high flood risk
        if flood_risk_level in ['High', 'Very High']:
            return "High Risk - Significant flood exposure threatening mortgage value"
        
        # Check for negative mortgage value
        if mortgage_value < 0:
            negative_pct = abs(mortgage_value) / loan_amount
            if negative_pct > 0.1:
                return "Critical Risk - Mortgage value severely impacted"
            elif negative_pct > 0.05:
                return "High Risk - Significant negative impact on mortgage value"
            elif negative_pct > 0.02:
                return "Moderate Risk - Some negative impact on mortgage value"
        
        # Check LTV combined with flood risk
        if ltv_ratio > 0.8 and flood_risk_level in ['Medium', 'High', 'Very High']:
            return "High Risk - High LTV with flood exposure"
        elif ltv_ratio > 0.7 and flood_risk_level in ['Medium', 'High']:
            return "Moderate Risk - Elevated LTV with some flood exposure"
        
        # Default assessments
        if flood_risk_level == 'Medium':
            return "Moderate Risk - Some flood exposure"
        elif flood_risk_level == 'Low':
            return "Low Risk - Limited flood exposure"
        else:
            return "Minimal Risk - No significant flood impact identified"
    
    def _get_overall_risk_color(self, flood_risk_level: str, mortgage_value: float, 
                              loan_amount: float, ltv_ratio: float) -> str:
        """Determine risk color based on flood risk level and mortgage value."""
        if flood_risk_level in ['High', 'Very High'] or (mortgage_value < 0 and abs(mortgage_value) > loan_amount * 0.05):
            return "red"
        elif flood_risk_level == 'Medium' or (mortgage_value < 0 and abs(mortgage_value) > loan_amount * 0.02):
            return "orange"
        elif flood_risk_level == 'Low':
            return "goldenrod"
        else:
            return "green"
    
    def create_complete_popup_content(self, prop: Dict[str, Any], property_id: str, 
                                    address: Dict[str, Any], coordinates: str, 
                                    flood_risk: str, thames_proximity: str, 
                                    ground_elevation: Any, elevation_estimated: bool, 
                                    property_value: Any, construction_year: Any, 
                                    property_age_factor: str, has_mortgage: bool, 
                                    mortgage_info: Optional[Dict[str, Any]] = None, 
                                    flood_info: Optional[Dict[str, Any]] = None,
                                    mortgage_risk_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Create the complete popup content by aggregating different sections.
        
        Args:
            Various property and mortgage data inputs
            
        Returns:
            Complete HTML string for the popup content
        """
        # Create header
        header = self.create_header("Property Analysis", f"ID: {property_id}")
        
        # Create property section
        property_section = self.create_property_section(
            prop, property_id, address, coordinates, construction_year, 
            property_age_factor, property_value, has_mortgage
        )
        
        # Create flood info section if available
        flood_section = self.create_flood_info_section(flood_info) if flood_info else ""
        
        # Create mortgage section if available
        mortgage_section = ""
        if has_mortgage and mortgage_info:
            mortgage_section = self.create_mortgage_section(
                mortgage_info, property_value, flood_info.get('risk_level', 'Unknown') if flood_info else 'Unknown'
            )
        
        # Create mortgage risk section if available
        mortgage_risk_section = ""
        if mortgage_risk_info:
            mortgage_risk_section = self.create_mortgage_risk_section(mortgage_risk_info)
        
        # Combine all sections
        content = header + property_section + flood_section + mortgage_section + mortgage_risk_section
        
        return self.create_popup_wrapper(content)
    
    def build_property_popup(self, prop: Dict[str, Any], property_id: str, 
                           address: Dict[str, Any], coordinates: str, 
                           flood_risk: str, thames_proximity: str, 
                           ground_elevation: Any, elevation_estimated: bool, 
                           property_value: Any, construction_year: Any, 
                           property_age_factor: str, has_mortgage: bool, 
                           mortgage_info: Optional[Dict[str, Any]] = None, 
                           flood_info: Optional[Dict[str, Any]] = None,
                           mortgage_risk_info: Optional[Dict[str, Any]] = None) -> folium.Popup:
        """
        Build a complete property popup.
        
        Args:
            Various property and mortgage data inputs
            
        Returns:
            Folium Popup object ready to be attached to a marker
        """
        content = self.create_complete_popup_content(
            prop, property_id, address, coordinates, flood_risk, thames_proximity,
            ground_elevation, elevation_estimated, property_value, construction_year,
            property_age_factor, has_mortgage, mortgage_info, flood_info, mortgage_risk_info
        )
        
        return self.build_popup(content)