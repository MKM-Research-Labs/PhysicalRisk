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

# src/utilities/page_02_location.py

"""
Page 2: Location Details
Handles comprehensive location information and geographic data.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class LocationPage(BasePage):
    """Generates location details page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate location page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Location Details", self.styles['SectionHeader']))
            
            header_data = property_data.get('PropertyHeader', {})
            location_data = header_data.get('Location', {})
            
            # PRIMARY ADDRESS SECTION
            elements.append(Paragraph("Primary Address", self.styles['SubSectionHeader']))
            
            address_data = [["Address Component", "Value"]]
            
            # Build full address
            address_parts = []
            address_fields = ['BuildingNumber', 'StreetName', 'TownCity', 'County', 'Postcode']
            for field in address_fields:
                value = location_data.get(field)
                if value:
                    address_parts.append(str(value))
            
            full_address = ", ".join(address_parts) if address_parts else "Unknown"
            address_data.append(["Full Address", full_address])
            
            # Individual address components
            address_components = [
                ('BuildingName', 'Building Name'),
                ('BuildingNumber', 'Building Number'),
                ('SubBuildingNumber', 'Sub Building Number'),
                ('SubBuildingName', 'Sub Building Name'),
                ('StreetName', 'Street Name'),
                ('TownCity', 'Town/City'),
                ('County', 'County'),
                ('Postcode', 'Postcode'),
                ('AddressLine2', 'Address Line 2')
            ]
            
            for field, label in address_components:
                value = location_data.get(field)
                if value:
                    address_data.append([label, self._format_value(value)])
            
            address_table = Table(address_data, colWidths=self.table_widths['two_col'])
            address_table.setStyle(self.table_styles['standard'])
            elements.append(address_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # GEOGRAPHIC COORDINATES SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Geographic Information", self.styles['SubSectionHeader']))
            
            geo_data = [["Geographic Detail", "Value"]]
            
            # Coordinates
            lat = location_data.get('LatitudeDegrees')
            lon = location_data.get('LongitudeDegrees')
            if lat is not None and lon is not None:
                geo_data.append(["Latitude", f"{lat}°N"])
                geo_data.append(["Longitude", f"{lon}°E"])
                geo_data.append(["Coordinates", f"{lat}°N, {lon}°E"])
            
            # Grid references and location codes
            grid_ref = location_data.get('BritishNationalGrid')
            if grid_ref:
                geo_data.append(["British National Grid", grid_ref])
            
            what3words = location_data.get('What3Words')
            if what3words:
                geo_data.append(["What3Words", what3words])
            
            usrn = location_data.get('USRN')
            if usrn:
                geo_data.append(["USRN", str(usrn)])
            
            geo_table = Table(geo_data, colWidths=self.table_widths['two_col'])
            geo_table.setStyle(self.table_styles['standard'])
            elements.append(geo_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ADMINISTRATIVE AREAS SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Administrative Areas", self.styles['SubSectionHeader']))
            
            admin_data = [["Administrative Detail", "Value"]]
            
            administrative_fields = [
                ('Country', 'Country'),
                ('Region', 'Region'),
                ('LocalAuthority', 'Local Authority'),
                ('ElectoralWard', 'Electoral Ward'),
                ('ParliamentaryConstituency', 'Parliamentary Constituency')
            ]
            
            for field, label in administrative_fields:
                value = location_data.get(field)
                if value:
                    admin_data.append([label, self._format_value(value)])
            
            admin_table = Table(admin_data, colWidths=self.table_widths['two_col'])
            admin_table.setStyle(self.table_styles['standard'])
            elements.append(admin_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # AREA CLASSIFICATION SECTION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Area Classification", self.styles['SubSectionHeader']))
            
            classification_data = [["Classification", "Value"]]
            
            # Urban/Rural classification
            urban_rural = location_data.get('UrbanRuralClassification')
            if urban_rural:
                classification_data.append(["Urban/Rural Classification", urban_rural])
            
            # Population density
            density = location_data.get('LocalDensityHectare')
            if isinstance(density, (int, float)):
                classification_data.append([
                    "Local Density", 
                    f"{density:.2f} per hectare"
                ])
                
                # Categorize density
                if density > 200:
                    density_category = "Very High Density"
                elif density > 100:
                    density_category = "High Density"
                elif density > 50:
                    density_category = "Medium Density"
                elif density > 20:
                    density_category = "Low-Medium Density"
                else:
                    density_category = "Low Density"
                    
                classification_data.append(["Density Category", density_category])
            
            classification_table = Table(classification_data, colWidths=self.table_widths['two_col'])
            classification_table.setStyle(self.table_styles['standard'])
            elements.append(classification_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating location details: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements