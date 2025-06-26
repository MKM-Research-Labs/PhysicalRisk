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

# src/utilities/page_03_attributes.py

"""
Page 3: Property Attributes
Handles property characteristics, dimensions, and physical attributes.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class AttributesPage(BasePage):
    """Generates property attributes page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate property attributes page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Property Attributes", self.styles['SectionHeader']))
            
            header_data = property_data.get('PropertyHeader', {})
            attributes_data = header_data.get('PropertyAttributes', {})
            
            # BASIC PROPERTY INFORMATION
            elements.append(Paragraph("Basic Property Information", self.styles['SubSectionHeader']))
            
            basic_data = [["Attribute", "Value"]]
            
            # Core property details
            basic_fields = [
                ('PropertyType', 'Property Type'),
                ('OccupancyType', 'Occupancy Type'),
                ('PropertyCondition', 'Property Condition'),
                ('PropertyResi', 'Property Classification'),
                ('BuildingResidency', 'Building Residency'),
                ('OccupancyResidency', 'Occupancy Residency')
            ]
            
            for field, label in basic_fields:
                value = attributes_data.get(field)
                if value:
                    basic_data.append([label, self._format_value(value)])
            
            basic_table = Table(basic_data, colWidths=self.table_widths['two_col'])
            basic_table.setStyle(self.table_styles['standard'])
            elements.append(basic_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # PHYSICAL DIMENSIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Physical Dimensions", self.styles['SubSectionHeader']))
            
            dimensions_data = [["Dimension", "Value"]]
            
            # Area and size measurements
            area = attributes_data.get('PropertyAreaSqm')
            if isinstance(area, (int, float)):
                dimensions_data.append(["Property Area", f"{area:.1f} sqm"])
            
            height = attributes_data.get('HeightMeters')
            if isinstance(height, (int, float)):
                dimensions_data.append(["Property Height", f"{height:.2f} m"])
            
            storeys = attributes_data.get('NumberOfStoreys')
            if isinstance(storeys, (int, float)):
                dimensions_data.append(["Number of Storeys", str(int(storeys))])
            
            total_rooms = attributes_data.get('TotalRooms')
            if isinstance(total_rooms, (int, float)):
                dimensions_data.append(["Total Rooms", str(int(total_rooms))])
            
            dimensions_table = Table(dimensions_data, colWidths=self.table_widths['two_col'])
            dimensions_table.setStyle(self.table_styles['standard'])
            elements.append(dimensions_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ROOM COMPOSITION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Room Composition", self.styles['SubSectionHeader']))
            
            rooms_data = [["Room Type", "Count"]]
            
            # Room counts
            room_fields = [
                ('NumberBedrooms', 'Bedrooms'),
                ('NumberBathrooms', 'Bathrooms')
            ]
            
            for field, label in room_fields:
                value = attributes_data.get(field)
                if isinstance(value, (int, float)):
                    rooms_data.append([label, str(int(value))])
            
            rooms_table = Table(rooms_data, colWidths=self.table_widths['two_col'])
            rooms_table.setStyle(self.table_styles['standard'])
            elements.append(rooms_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # BUILDING AGE AND PERIOD
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Building Age & Period", self.styles['SubSectionHeader']))
            
            age_data = [["Age Information", "Value"]]
            
            # Construction year and calculated age
            construction_year = attributes_data.get('ConstructionYear')
            if construction_year and isinstance(construction_year, (int, float)):
                age_data.append(["Construction Year", str(int(construction_year))])
                
                building_age = datetime.now().year - int(construction_year)
                age_data.append(["Building Age", f"{building_age} years"])
                
                # Age risk categorization
                if building_age > 100:
                    age_category = "Historic (Pre-1925)"
                    risk_level = "High maintenance risk"
                elif building_age > 50:
                    age_category = "Mature (1925-1975)"
                    risk_level = "Medium maintenance risk"
                elif building_age > 25:
                    age_category = "Modern (1975-2000)"
                    risk_level = "Low maintenance risk"
                else:
                    age_category = "Contemporary (Post-2000)"
                    risk_level = "Very low maintenance risk"
                
                age_data.append(["Age Category", age_category])
                age_data.append(["Maintenance Risk", risk_level])
            
            # Property period
            property_period = attributes_data.get('PropertyPeriod')
            if property_period:
                age_data.append(["Property Period", property_period])
            
            age_table = Table(age_data, colWidths=self.table_widths['two_col'])
            age_table.setStyle(self.table_styles['standard'])
            elements.append(age_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # EXTERNAL FEATURES
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("External Features", self.styles['SubSectionHeader']))
            
            external_data = [["Feature", "Details"]]
            
            # Parking
            parking_type = attributes_data.get('ParkingType')
            if parking_type:
                external_data.append(["Parking Type", parking_type])
            
            # Access
            access_type = attributes_data.get('AccessType')
            if access_type:
                external_data.append(["Access Type", access_type])
            
            # Garden areas
            garden_front = attributes_data.get('GardenAreaFront')
            if isinstance(garden_front, (int, float)):
                external_data.append(["Front Garden Area", f"{garden_front:.1f} sqm"])
            
            garden_back = attributes_data.get('GardenAreaBack')
            if isinstance(garden_back, (int, float)):
                external_data.append(["Back Garden Area", f"{garden_back:.1f} sqm"])
            
            external_table = Table(external_data, colWidths=self.table_widths['two_col'])
            external_table.setStyle(self.table_styles['standard'])
            elements.append(external_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # FINANCIAL AND ADMINISTRATIVE
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Financial & Administrative", self.styles['SubSectionHeader']))
            
            financial_data = [["Category", "Status/Value"]]
            
            # Council tax
            council_tax_band = attributes_data.get('CouncilTaxBand')
            if council_tax_band:
                financial_data.append(["Council Tax Band", council_tax_band])
            
            # Various flags
            flag_fields = [
                ('HousingAssociation', 'Housing Association Property'),
                ('IncomeGenerating', 'Income Generating'),
                ('PayingBusinessRates', 'Pays Business Rates')
            ]
            
            for field, label in flag_fields:
                value = attributes_data.get(field)
                if value is not None:
                    financial_data.append([label, self._format_value(value)])
            
            financial_table = Table(financial_data, colWidths=self.table_widths['two_col'])
            financial_table.setStyle(self.table_styles['financial'])
            elements.append(financial_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # MAINTENANCE AND CONDITION
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Maintenance & Condition", self.styles['SubSectionHeader']))
            
            maintenance_data = [["Maintenance Item", "Status/Date"]]
            
            # Last major works
            last_works = attributes_data.get('LastMajorWorksDate')
            if last_works:
                maintenance_data.append(["Last Major Works", last_works])
            
            # Renovation required
            renovation_required = attributes_data.get('RenovationRequired')
            if renovation_required is not None:
                maintenance_data.append(["Renovation Required", self._format_value(renovation_required)])
            
            # Property condition (already shown above but important for maintenance context)
            condition = attributes_data.get('PropertyCondition')
            if condition:
                maintenance_data.append(["Current Condition", condition])
                
                # Condition-based recommendations
                if condition.lower() in ['very poor', 'poor']:
                    recommendation = "Immediate attention required"
                elif condition.lower() in ['fair', 'average']:
                    recommendation = "Moderate maintenance needed"
                elif condition.lower() in ['good', 'very good']:
                    recommendation = "Regular maintenance sufficient"
                else:
                    recommendation = "Assessment recommended"
                
                maintenance_data.append(["Maintenance Priority", recommendation])
            
            maintenance_table = Table(maintenance_data, colWidths=self.table_widths['two_col'])
            maintenance_table.setStyle(self.table_styles['standard'])
            elements.append(maintenance_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating property attributes: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements