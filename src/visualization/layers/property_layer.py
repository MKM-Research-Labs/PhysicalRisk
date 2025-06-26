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
Property layer module for property visualization.

This module provides functionality for adding property markers with
risk indicators, mortgage status, and detailed analysis popups.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import folium

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Import utils
try:
    from ..utils import ColorSchemes, DataFormatter, DataExtractor, RiskAssessor
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(current_file.parent.parent))
    from utils import ColorSchemes, DataFormatter, DataExtractor, RiskAssessor


class PropertyLayer:
    """
    Layer class for adding property markers and risk analysis to the map.
    
    This class handles the creation of property markers with flood risk coloring,
    mortgage status indicators, and comprehensive property information popups.
    """
    
    def __init__(self):
        """Initialize the property layer."""
        self.layer_name = "Properties"
        self.show_risk_colors = True
        self.show_mortgage_status = True
        self.risk_based_sizing = False
    
    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """
        Add property layer to the map.
        
        Args:
            folium_map: The Folium map to add the layer to
            loaded_data: LoadedData container with all data
            
        Returns:
            FeatureGroup containing all property elements
        """
        print(f"Adding {self.layer_name} to map...")
        
        # Create feature group for property elements
        property_group = folium.FeatureGroup(name=self.layer_name)
        
        if not loaded_data.property_data:
            print("⚠️  No property data available")
            return property_group
        
        # Extract properties
        properties = self._get_properties_list(loaded_data.property_data)
        
        if not properties:
            print("⚠️  No valid property data found")
            return property_group
        
        property_count = 0
        mortgaged_property_count = 0
        
        # Process each property
        for prop in properties:
            try:
                # Extract property information
                property_info = DataExtractor.extract_property_info(prop)
                if property_info is None:
                    continue
                
                lat = property_info['coordinates']['latitude']
                lon = property_info['coordinates']['longitude']
                
                if lat is not None and lon is not None:
                    property_count += 1
                    property_id = property_info['property_id']
                    
                    # Get related data
                    property_flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}
                    has_mortgage = property_id in (loaded_data.mortgage_lookup or {})
                    mortgage_info = loaded_data.mortgage_lookup.get(property_id, {}) if loaded_data.mortgage_lookup else {}
                    
                    if has_mortgage:
                        mortgaged_property_count += 1
                    
                    # Add property marker
                    self._add_property_marker(property_group, property_info, property_flood_info, 
                                            has_mortgage, mortgage_info, loaded_data)
                    
            except Exception as e:
                print(f"Warning: Error processing property: {e}")
                continue
        
        # Add to map
        property_group.add_to(folium_map)
        
        print(f"✓ Added {property_count} properties to map ({mortgaged_property_count} with mortgages)")
        return property_group
    
    def _add_property_marker(self, feature_group: folium.FeatureGroup, property_info: Dict[str, Any],
                           property_flood_info: Dict[str, Any], has_mortgage: bool,
                           mortgage_info: Dict[str, Any], loaded_data) -> None:
        """
        Add a single property marker to the feature group.
        
        Args:
            feature_group: Folium FeatureGroup to add the marker to
            property_info: Extracted property information
            property_flood_info: Flood risk information for this property
            has_mortgage: Whether the property has a mortgage
            mortgage_info: Mortgage information if available
            loaded_data: Full loaded data for mortgage risk lookup
        """
        try:
            lat = property_info['coordinates']['latitude']
            lon = property_info['coordinates']['longitude']
            property_id = property_info['property_id']
            
            # Get mortgage risk information if available
            mortgage_risk_info = None
            if has_mortgage and loaded_data.mortgage_risk_info:
                mortgage_risk_info = loaded_data.mortgage_risk_info.get('by_property_id', {}).get(property_id)
            
            # Create popup content
            popup_content = self._create_property_popup(
                property_info, property_flood_info, has_mortgage, 
                mortgage_info, mortgage_risk_info
            )
            
            # Create tooltip
            flood_risk = property_flood_info.get('risk_level', property_info.get('flood_risk', 'Unknown'))
            tooltip = f"Property: {property_id} | Risk: {flood_risk}{' | Mortgaged' if has_mortgage else ''}"
            
            # Determine marker icon and color
            icon = self._get_property_icon(property_info, flood_risk, has_mortgage)
            
            # Create marker
            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=350),
                tooltip=tooltip,
                icon=icon
            )
            
            marker.add_to(feature_group)
            
        except Exception as e:
            print(f"Warning: Error creating property marker for {property_info.get('property_id', 'Unknown')}: {e}")
    
    def _create_property_popup(self, property_info: Dict[str, Any], property_flood_info: Dict[str, Any],
                             has_mortgage: bool, mortgage_info: Dict[str, Any],
                             mortgage_risk_info: Optional[Dict[str, Any]]) -> str:
        """
        Create comprehensive popup content for a property marker.
        
        Args:
            property_info: Extracted property information
            property_flood_info: Flood risk information
            has_mortgage: Whether property has mortgage
            mortgage_info: Mortgage information
            mortgage_risk_info: Mortgage risk analysis
            
        Returns:
            HTML string for popup content
        """
        property_id = property_info['property_id']
        coordinates = DataFormatter.format_coordinates(
            property_info['coordinates']['latitude'],
            property_info['coordinates']['longitude']
        )
        
        # Start popup
        popup_content = f"""
        <div style="font-family: Arial; width: 320px; max-height: 400px; overflow-y: auto;">
            <h4 style="margin-bottom: 5px; color: #1a5276;">Property Analysis</h4>
            <p style="color: #566573; font-size: 0.9em;">ID: {property_id}</p>
        """
        
        # Property information section
        popup_content += self._create_property_section(property_info, coordinates)
        
        # Flood risk section if available
        if property_flood_info:
            popup_content += self._create_flood_section(property_flood_info)
        
        # Mortgage section if available
        if has_mortgage and mortgage_info:
            popup_content += self._create_mortgage_section(mortgage_info, property_info.get('property_value'))
        
        # Mortgage risk section if available
        if mortgage_risk_info:
            popup_content += self._create_mortgage_risk_section(mortgage_risk_info)
        
        popup_content += "</div>"
        return popup_content
    
    def _create_property_section(self, property_info: Dict[str, Any], coordinates: str) -> str:
        """Create the property information section."""
        formatted_address = DataFormatter.format_address(property_info['address'])
        property_value = DataFormatter.format_currency(property_info.get('property_value', 'Unknown'))
        
        return f"""
        <div style="background-color: #EBF5FB; padding: 10px; border-radius: 5px; margin-top: 10px;">
            <h5 style="margin-top: 0; color: #1a5276;">Property Information</h5>
            <p><b>Type:</b> {property_info.get('property_type', 'Unknown')}</p>
            <p><b>Status:</b> {property_info.get('property_status', 'Unknown')}</p>
            <p><b>Building Type:</b> {property_info.get('building_type', 'Unknown')}</p>
            <p><b>Address:</b> {formatted_address}</p>
            <p><b>Coordinates:</b> {coordinates}</p>
            <p><b>Construction Year:</b> {property_info.get('construction_year', 'Unknown')} ({property_info.get('property_age_factor', 'Unknown')})</p>
            <p><b>Storeys:</b> {property_info.get('number_of_storeys', 'Unknown')}</p>
            <p><b>Construction Type:</b> {property_info.get('construction_type', 'Unknown')}</p>
            <p><b>Property Value:</b> {property_value}</p>
        </div>
        """
    
    def _create_flood_section(self, property_flood_info: Dict[str, Any]) -> str:
        """Create the flood risk information section."""
        risk_level = property_flood_info.get('risk_level', 'Unknown')
        risk_color = ColorSchemes.get_flood_risk_color(risk_level)
        
        return f"""
        <div style="background-color: #D5F5E3; padding: 10px; border-radius: 5px; margin-top: 10px;">
            <h5 style="margin-top: 0; color: #1E8449;">Flood Risk Assessment</h5>
            <p><b>Nearest Gauge:</b> {property_flood_info.get('nearest_gauge', 'N/A')}</p>
            <p><b>Distance to Gauge:</b> {DataFormatter.safe_format_float(property_flood_info.get('distance_to_gauge', 0), 2)} km</p>
            <p><b>Property Elevation:</b> {DataFormatter.safe_format_float(property_flood_info.get('property_elevation', 0), 2)} m</p>
            <p><b>Water Level:</b> {DataFormatter.safe_format_float(property_flood_info.get('water_level', 0), 2)} m</p>
            <p><b>Flood Depth:</b> {DataFormatter.safe_format_float(property_flood_info.get('flood_depth', 0), 2)} m</p>
            <p><b>Risk Level:</b> <span style="color: {risk_color}; font-weight: bold;">{risk_level}</span></p>
            <p><b>Value at Risk:</b> {DataFormatter.format_currency(property_flood_info.get('value_at_risk', 0))}</p>
        </div>
        """
    
    def _create_mortgage_section(self, mortgage_info: Dict[str, Any], property_value: Any) -> str:
        """Create the mortgage information section."""
        # Extract financial information with fallbacks
        loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
        interest_rate = mortgage_info.get('original_lending_rate', mortgage_info.get('OriginalLendingRate', 0))
        term_years = mortgage_info.get('term_years', mortgage_info.get('TermYears', 'N/A'))
        provider = mortgage_info.get('mortgage_provider', mortgage_info.get('MortgageProvider', 'N/A'))
        
        # Calculate LTV
        ltv_ratio = 0
        if loan_amount and property_value:
            try:
                ltv_ratio = float(loan_amount) / float(property_value)
            except (ValueError, TypeError, ZeroDivisionError):
                ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
        
        return f"""
        <div style="margin-top: 20px; border-top: 3px solid #8E44AD; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD; text-align: center; background-color: #E8DAEF; padding: 5px; border-radius: 5px;">MORTGAGE DETAILS</h4>
            
            <div style="background-color: #E8DAEF; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #6C3483;">Loan Information</h5>
                <p><b>Lender:</b> {provider}</p>
                <p><b>Loan Amount:</b> {DataFormatter.format_currency(loan_amount)}</p>
                <p><b>Interest Rate:</b> {DataFormatter.safe_format_float(interest_rate * 100 if interest_rate and interest_rate < 1 else interest_rate, 2)}%</p>
                <p><b>Term:</b> {term_years} years</p>
                <p><b>LTV Ratio:</b> {DataFormatter.format_percentage(ltv_ratio)}</p>
            </div>
        </div>
        """
    
    def _create_mortgage_risk_section(self, mortgage_risk_info: Dict[str, Any]) -> str:
        """Create the mortgage risk analysis section."""
        flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
        mortgage_value = mortgage_risk_info.get('mortgage_value', 0)
        loan_amount = mortgage_risk_info.get('loan_amount', 0)
        
        # Generate risk assessment
        ltv_ratio = mortgage_risk_info.get('loan_amount', 0) / mortgage_risk_info.get('property_value', 1) if mortgage_risk_info.get('property_value', 0) > 0 else 0
        risk_summary = RiskAssessor.assess_mortgage_risk(flood_risk_level, mortgage_value, loan_amount, ltv_ratio)
        
        return f"""
        <div style="margin-top: 20px; border-top: 3px solid #5DADE2; padding-top: 10px;">
            <h4 style="margin-bottom: 5px; color: #2E86C1; text-align: center; background-color: #D6EAF8; padding: 5px; border-radius: 5px;">MORTGAGE RISK ANALYSIS</h4>
            
            <div style="background-color: #D6EAF8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #2874A6;">Risk Metrics</h5>
                <p><b>Mortgage Value:</b> {DataFormatter.format_currency(mortgage_value)}</p>
                <p><b>Value at Risk:</b> {DataFormatter.format_currency(mortgage_risk_info.get('mortgage_value_at_risk', 0))}</p>
                <p><b>Flood Risk Level:</b> <span style="color: {ColorSchemes.get_flood_risk_color(flood_risk_level)}; font-weight: bold;">{flood_risk_level}</span></p>
                <p><b>Flood Depth:</b> {DataFormatter.safe_format_float(mortgage_risk_info.get('flood_depth', 0), 2)} m</p>
            </div>
            
            <div style="background-color: #FADBD8; padding: 10px; border-radius: 5px; margin-top: 10px;">
                <h5 style="margin-top: 0; color: #943126;">Risk Assessment</h5>
                <p><b>Overall Assessment:</b> <span style="font-weight: bold;">{risk_summary}</span></p>
            </div>
        </div>
        """
    
    def _get_property_icon(self, property_info: Dict[str, Any], flood_risk: str, has_mortgage: bool) -> folium.Icon:
        """
        Determine the appropriate icon for a property marker.
        
        Args:
            property_info: Property information
            flood_risk: Flood risk level
            has_mortgage: Whether property has mortgage
            
        Returns:
            Folium Icon object
        """
        # Determine color based on flood risk
        if self.show_risk_colors:
            color = ColorSchemes.get_folium_color_name(ColorSchemes.get_flood_risk_color(flood_risk))
        else:
            color = 'blue'
        
        # Determine icon based on mortgage status
        if self.show_mortgage_status and has_mortgage:
            icon_type = 'university'  # Bank/mortgage icon
        else:
            icon_type = 'home'
        
        return folium.Icon(color=color, icon=icon_type, prefix='fa')
    
    def _get_properties_list(self, property_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract properties list from property data.
        
        Args:
            property_data: Raw property data
            
        Returns:
            List of property dictionaries
        """
        if isinstance(property_data, dict):
            properties = property_data.get('properties') or []
            if not properties and 'PropertyHeader' in property_data:
                properties = [property_data]
            elif not properties:
                properties = property_data.get('portfolio', [])
        elif isinstance(property_data, list):
            properties = property_data
        else:
            print(f"Warning: Unexpected property data type: {type(property_data)}")
            properties = []
        
        return properties
    
    def configure(self, show_risk_colors: bool = True, show_mortgage_status: bool = True,
                 risk_based_sizing: bool = False):
        """
        Configure property layer display options.
        
        Args:
            show_risk_colors: Whether to color markers based on flood risk
            show_mortgage_status: Whether to show mortgage status in icons
            risk_based_sizing: Whether to size markers based on risk level
        """
        self.show_risk_colors = show_risk_colors
        self.show_mortgage_status = show_mortgage_status
        self.risk_based_sizing = risk_based_sizing
        
        print(f"✓ Property layer configured: risk_colors={show_risk_colors}, mortgage={show_mortgage_status}, sizing={risk_based_sizing}")
    
    def get_property_statistics(self, properties: List[Dict[str, Any]], loaded_data) -> Dict[str, Any]:
        """
        Calculate statistics for the properties.
        
        Args:
            properties: List of property data
            loaded_data: Full loaded data
            
        Returns:
            Dictionary with property statistics
        """
        if not properties:
            return {}
        
        # Count by risk level
        risk_counts = {}
        mortgage_count = 0
        
        for prop in properties:
            try:
                property_info = DataExtractor.extract_property_info(prop)
                if property_info:
                    property_id = property_info['property_id']
                    
                    # Get flood risk
                    flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}
                    risk_level = flood_info.get('risk_level', property_info.get('flood_risk', 'Unknown'))
                    risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
                    
                    # Check mortgage
                    if property_id in (loaded_data.mortgage_lookup or {}):
                        mortgage_count += 1
            except Exception:
                continue
        
        return {
            'total_properties': len(properties),
            'mortgaged_properties': mortgage_count,
            'mortgage_percentage': (mortgage_count / len(properties)) * 100,
            'risk_distribution': risk_counts
        }