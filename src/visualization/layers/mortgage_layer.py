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
Mortgage layer module for mortgage risk visualization.

This module provides functionality for adding mortgage-related overlays
including risk circles, LTV indicators, and financial risk visualization.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import folium
import numpy as np

# Fix the Python path to find project modules
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import modules
from src.utilities.project_paths import ProjectPaths

# Import utils
try:
    from ..utils import ColorSchemes, DataFormatter, RiskAssessor
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(current_file.parent.parent))
    from utils import ColorSchemes, DataFormatter, RiskAssessor


class MortgageLayer:
    """
    Layer class for adding mortgage risk visualization overlays to the map.
    
    This class handles the creation of mortgage risk circles, LTV indicators,
    and financial risk visualization elements.
    """
    
    def __init__(self):
        """Initialize the mortgage layer."""
        self.layer_name = "Mortgage Risk"
        self.show_risk_circles = True
        self.show_ltv_indicators = True
        self.circle_opacity = 0.4
        self.max_circle_radius = 500  # meters
    
    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """
        Add mortgage layer to the map.
        
        Args:
            folium_map: The Folium map to add the layer to
            loaded_data: LoadedData container with all data
            
        Returns:
            FeatureGroup containing all mortgage elements
        """
        print(f"Adding {self.layer_name} to map...")
        
        # Create feature group for mortgage elements
        mortgage_group = folium.FeatureGroup(name=self.layer_name)
        
        if not loaded_data.mortgage_data or not loaded_data.property_data:
            print("⚠️  Insufficient data for mortgage layer (need both mortgage and property data)")
            return mortgage_group
        
        # Extract mortgage information with property locations
        mortgage_locations = self._extract_mortgage_locations(loaded_data)
        
        if not mortgage_locations:
            print("⚠️  No valid mortgage location data found")
            return mortgage_group
        
        # Add mortgage risk circles
        if self.show_risk_circles:
            self._add_mortgage_risk_circles(mortgage_group, mortgage_locations)
        
        # Add LTV indicators
        if self.show_ltv_indicators:
            self._add_ltv_indicators(mortgage_group, mortgage_locations)
        
        # Add to map
        mortgage_group.add_to(folium_map)
        
        print(f"✓ Added {len(mortgage_locations)} mortgage risk indicators to map")
        return mortgage_group
    
    def _extract_mortgage_locations(self, loaded_data) -> List[Dict[str, Any]]:
        """
        Extract mortgage information combined with property locations.
        
        Args:
            loaded_data: LoadedData container
            
        Returns:
            List of mortgage data with location information
        """
        mortgage_locations = []
        
        if not loaded_data.mortgage_lookup:
            return mortgage_locations
        
        # Get property locations
        properties = self._get_properties_list(loaded_data.property_data)
        property_coords = {}
        
        # Build property coordinate lookup
        for prop in properties:
            try:
                header = prop.get('PropertyHeader', {}).get('Header', {})
                property_id = header.get('PropertyID')
                location = prop.get('PropertyHeader', {}).get('Location', {})
                lat = location.get('LatitudeDegrees') or location.get('Latitude')
                lon = location.get('LongitudeDegrees') or location.get('Longitude')
                
                if property_id and lat is not None and lon is not None:
                    property_coords[property_id] = {'lat': float(lat), 'lon': float(lon)}
            except Exception:
                continue
        
        # Combine mortgage data with coordinates
        for property_id, mortgage_info in loaded_data.mortgage_lookup.items():
            if property_id in property_coords:
                try:
                    # Get mortgage risk info if available
                    mortgage_risk_info = None
                    if loaded_data.mortgage_risk_info and 'by_property_id' in loaded_data.mortgage_risk_info:
                        mortgage_risk_info = loaded_data.mortgage_risk_info['by_property_id'].get(property_id)
                    
                    # Get property flood info
                    property_flood_info = loaded_data.property_flood_info.get(property_id, {}) if loaded_data.property_flood_info else {}
                    
                    mortgage_location = {
                        'property_id': property_id,
                        'lat': property_coords[property_id]['lat'],
                        'lon': property_coords[property_id]['lon'],
                        'mortgage_info': mortgage_info,
                        'mortgage_risk_info': mortgage_risk_info,
                        'property_flood_info': property_flood_info
                    }
                    
                    mortgage_locations.append(mortgage_location)
                    
                except Exception as e:
                    print(f"Warning: Error processing mortgage for property {property_id}: {e}")
                    continue
        
        return mortgage_locations
    
    def _add_mortgage_risk_circles(self, feature_group: folium.FeatureGroup, 
                                  mortgage_locations: List[Dict[str, Any]]):
        """
        Add mortgage risk circles to show loan amounts and risk levels.
        
        Args:
            feature_group: Folium FeatureGroup to add circles to
            mortgage_locations: List of mortgage location data
        """
        # Calculate loan amount range for circle sizing
        loan_amounts = []
        for location in mortgage_locations:
            mortgage_info = location['mortgage_info']
            loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
            if loan_amount and loan_amount > 0:
                loan_amounts.append(float(loan_amount))
        
        if not loan_amounts:
            print("⚠️  No valid loan amounts found for risk circles")
            return
        
        min_loan = min(loan_amounts)
        max_loan = max(loan_amounts)
        
        circles_added = 0
        
        for location in mortgage_locations:
            try:
                mortgage_info = location['mortgage_info']
                mortgage_risk_info = location['mortgage_risk_info']
                property_flood_info = location['property_flood_info']
                
                # Get loan amount
                loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
                if not loan_amount or loan_amount <= 0:
                    continue
                
                # Calculate circle radius based on loan amount
                if max_loan > min_loan:
                    norm_amount = (float(loan_amount) - min_loan) / (max_loan - min_loan)
                else:
                    norm_amount = 0.5
                
                radius = 50 + (norm_amount * (self.max_circle_radius - 50))  # 50m to max_circle_radius
                
                # Determine circle color based on risk
                circle_color = self._get_mortgage_risk_color(mortgage_info, mortgage_risk_info, property_flood_info)
                
                # Create popup content
                popup_content = self._create_mortgage_circle_popup(location)
                
                # Create circle
                circle = folium.Circle(
                    location=[location['lat'], location['lon']],
                    radius=radius,
                    color=circle_color,
                    fill=True,
                    fillColor=circle_color,
                    fillOpacity=self.circle_opacity,
                    weight=2,
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"Mortgage: {DataFormatter.format_currency(loan_amount)} | Risk Circle"
                )
                
                circle.add_to(feature_group)
                circles_added += 1
                
            except Exception as e:
                print(f"Warning: Error creating mortgage circle: {e}")
                continue
        
        print(f"✓ Added {circles_added} mortgage risk circles")
    
    def _add_ltv_indicators(self, feature_group: folium.FeatureGroup,
                           mortgage_locations: List[Dict[str, Any]]):
        """
        Add LTV (Loan-to-Value) ratio indicators as small markers.
        
        Args:
            feature_group: Folium FeatureGroup to add indicators to
            mortgage_locations: List of mortgage location data
        """
        indicators_added = 0
        
        for location in mortgage_locations:
            try:
                mortgage_info = location['mortgage_info']
                
                # Calculate LTV ratio
                loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
                ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
                
                if not ltv_ratio and loan_amount:
                    # Try to calculate from property value if available
                    # This would need property value data - skip for now if not available
                    continue
                
                if not ltv_ratio:
                    continue
                
                # Ensure LTV is in 0-1 range
                if ltv_ratio > 1:
                    ltv_ratio = ltv_ratio / 100
                
                # Determine LTV risk color
                ltv_color = ColorSchemes.get_ltv_risk_color(ltv_ratio)
                
                # Create small LTV indicator marker (offset slightly from property)
                ltv_marker = folium.CircleMarker(
                    location=[location['lat'] + 0.0001, location['lon'] + 0.0001],  # Small offset
                    radius=4,
                    color=ltv_color,
                    fill=True,
                    fillColor=ltv_color,
                    fillOpacity=0.8,
                    weight=1,
                    popup=f"LTV Ratio: {DataFormatter.format_percentage(ltv_ratio)}",
                    tooltip=f"LTV: {DataFormatter.format_percentage(ltv_ratio)}"
                )
                
                ltv_marker.add_to(feature_group)
                indicators_added += 1
                
            except Exception as e:
                print(f"Warning: Error creating LTV indicator: {e}")
                continue
        
        print(f"✓ Added {indicators_added} LTV indicators")
    
    def _get_mortgage_risk_color(self, mortgage_info: Dict[str, Any], 
                                mortgage_risk_info: Optional[Dict[str, Any]],
                                property_flood_info: Dict[str, Any]) -> str:
        """
        Determine the appropriate color for a mortgage risk circle.
        
        Args:
            mortgage_info: Basic mortgage information
            mortgage_risk_info: Detailed risk analysis
            property_flood_info: Property flood risk information
            
        Returns:
            Color string for the circle
        """
        # Use mortgage risk info if available
        if mortgage_risk_info:
            flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
            return ColorSchemes.get_flood_risk_color(flood_risk_level)
        
        # Use property flood info if available
        if property_flood_info:
            risk_level = property_flood_info.get('risk_level', 'Unknown')
            return ColorSchemes.get_flood_risk_color(risk_level)
        
        # Fall back to LTV-based coloring
        ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
        if ltv_ratio:
            if ltv_ratio > 1:
                ltv_ratio = ltv_ratio / 100
            return ColorSchemes.get_ltv_risk_color(ltv_ratio)
        
        # Default color
        return '#2196F3'  # Blue
    
    def _create_mortgage_circle_popup(self, location: Dict[str, Any]) -> str:
        """
        Create popup content for mortgage risk circles.
        
        Args:
            location: Mortgage location data
            
        Returns:
            HTML string for popup content
        """
        mortgage_info = location['mortgage_info']
        mortgage_risk_info = location['mortgage_risk_info']
        property_flood_info = location['property_flood_info']
        
        # Extract basic mortgage data
        loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
        interest_rate = mortgage_info.get('original_lending_rate', mortgage_info.get('OriginalLendingRate', 0))
        ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
        
        popup_content = f"""
        <div style="font-family: Arial; width: 280px;">
            <h4 style="margin-bottom: 5px; color: #8E44AD;">Mortgage Risk Circle</h4>
            <p style="color: #566573; font-size: 0.9em;">Property: {location['property_id']}</p>
            
            <div style="background-color: #E8DAEF; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #6C3483;">Loan Details</h5>
                <p style="margin: 2px 0;"><b>Amount:</b> {DataFormatter.format_currency(loan_amount)}</p>
                <p style="margin: 2px 0;"><b>Interest Rate:</b> {DataFormatter.safe_format_float(interest_rate * 100 if interest_rate and interest_rate < 1 else interest_rate, 2)}%</p>
                <p style="margin: 2px 0;"><b>LTV Ratio:</b> {DataFormatter.format_percentage(ltv_ratio)}</p>
            </div>
        """
        
        # Add risk assessment if available
        if mortgage_risk_info:
            mortgage_value = mortgage_risk_info.get('mortgage_value', 0)
            flood_risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
            
            popup_content += f"""
            <div style="background-color: #FADBD8; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #943126;">Risk Assessment</h5>
                <p style="margin: 2px 0;"><b>Mortgage Value:</b> {DataFormatter.format_currency(mortgage_value)}</p>
                <p style="margin: 2px 0;"><b>Flood Risk:</b> <span style="color: {ColorSchemes.get_flood_risk_color(flood_risk_level)}; font-weight: bold;">{flood_risk_level}</span></p>
                <p style="margin: 2px 0;"><b>Value at Risk:</b> {DataFormatter.format_currency(mortgage_risk_info.get('mortgage_value_at_risk', 0))}</p>
            </div>
            """
        
        # Add flood info if available
        if property_flood_info:
            popup_content += f"""
            <div style="background-color: #D5F5E3; padding: 8px; border-radius: 5px; margin-top: 8px;">
                <h5 style="margin: 0 0 5px 0; color: #1E8449;">Flood Context</h5>
                <p style="margin: 2px 0;"><b>Flood Depth:</b> {DataFormatter.safe_format_float(property_flood_info.get('flood_depth', 0), 2)} m</p>
                <p style="margin: 2px 0;"><b>Risk Level:</b> {property_flood_info.get('risk_level', 'Unknown')}</p>
            </div>
            """
        
        popup_content += "</div>"
        return popup_content
    
    def _get_properties_list(self, property_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract properties list from property data."""
        if isinstance(property_data, dict):
            properties = property_data.get('properties') or []
            if not properties and 'PropertyHeader' in property_data:
                properties = [property_data]
            elif not properties:
                properties = property_data.get('portfolio', [])
        elif isinstance(property_data, list):
            properties = property_data
        else:
            properties = []
        
        return properties
    
    def configure(self, show_risk_circles: bool = True, show_ltv_indicators: bool = True,
                 circle_opacity: float = 0.4, max_circle_radius: int = 500):
        """
        Configure mortgage layer display options.
        
        Args:
            show_risk_circles: Whether to show mortgage risk circles
            show_ltv_indicators: Whether to show LTV ratio indicators
            circle_opacity: Opacity of risk circles (0-1)
            max_circle_radius: Maximum radius for risk circles in meters
        """
        self.show_risk_circles = show_risk_circles
        self.show_ltv_indicators = show_ltv_indicators
        self.circle_opacity = circle_opacity
        self.max_circle_radius = max_circle_radius
        
        print(f"✓ Mortgage layer configured: circles={show_risk_circles}, ltv={show_ltv_indicators}, "
              f"opacity={circle_opacity}, max_radius={max_circle_radius}")
    
    def get_mortgage_statistics(self, mortgage_locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for mortgages.
        
        Args:
            mortgage_locations: List of mortgage location data
            
        Returns:
            Dictionary with mortgage statistics
        """
        if not mortgage_locations:
            return {}
        
        loan_amounts = []
        ltv_ratios = []
        risk_levels = []
        
        for location in mortgage_locations:
            mortgage_info = location['mortgage_info']
            mortgage_risk_info = location['mortgage_risk_info']
            
            # Loan amounts
            loan_amount = mortgage_info.get('original_loan', mortgage_info.get('OriginalLoan', 0))
            if loan_amount and loan_amount > 0:
                loan_amounts.append(float(loan_amount))
            
            # LTV ratios
            ltv_ratio = mortgage_info.get('loan_to_value_ratio', mortgage_info.get('LoanToValueRatio', 0))
            if ltv_ratio:
                if ltv_ratio > 1:
                    ltv_ratio = ltv_ratio / 100
                ltv_ratios.append(ltv_ratio)
            
            # Risk levels
            if mortgage_risk_info:
                risk_level = mortgage_risk_info.get('flood_risk_level', 'Unknown')
                risk_levels.append(risk_level)
        
        # Calculate statistics
        stats = {
            'total_mortgages': len(mortgage_locations),
            'avg_loan_amount': np.mean(loan_amounts) if loan_amounts else 0,
            'total_loan_value': sum(loan_amounts) if loan_amounts else 0,
            'avg_ltv_ratio': np.mean(ltv_ratios) if ltv_ratios else 0,
            'high_ltv_count': len([r for r in ltv_ratios if r > 0.8]),
        }
        
        # Risk distribution
        risk_counts = {}
        for risk in risk_levels:
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        stats['risk_distribution'] = risk_counts
        
        return stats