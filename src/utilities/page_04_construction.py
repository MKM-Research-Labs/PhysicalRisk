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

# src/utilities/page_04_construction.py

"""
Page 4: Construction Details
Handles construction methods, materials, and structural information.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class ConstructionPage(BasePage):
    """Generates construction details page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate construction details page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Construction Details", self.styles['SectionHeader']))
            
            header_data = property_data.get('PropertyHeader', {})
            construction_data = header_data.get('Construction', {})
            
            if not construction_data:
                elements.append(Paragraph("No construction data available.", self.styles['Normal']))
                return elements
            
            # CONSTRUCTION METHODS
            elements.append(Paragraph("Construction Methods", self.styles['SubSectionHeader']))
            
            methods_data = [["Construction Aspect", "Details"]]
            
            # Construction type and materials
            construction_fields = [
                ('ConstructionType', 'Construction Type'),
                ('FoundationType', 'Foundation Type'),
                ('FloorType', 'Floor Type')
            ]
            
            for field, label in construction_fields:
                value = construction_data.get(field)
                if value:
                    methods_data.append([label, self._format_value(value)])
            
            methods_table = Table(methods_data, colWidths=self.table_widths['two_col'])
            methods_table.setStyle(self.table_styles['standard'])
            elements.append(methods_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # STRUCTURAL DIMENSIONS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Structural Dimensions", self.styles['SubSectionHeader']))
            
            dimensions_data = [["Dimension", "Measurement"]]
            
            # Height measurements
            property_height = construction_data.get('PropertyHeight')
            if isinstance(property_height, (int, float)):
                dimensions_data.append(["Property Height", f"{property_height:.2f} m"])
            
            floor_level = construction_data.get('FloorLevelMeters')
            if isinstance(floor_level, (int, float)):
                dimensions_data.append(["Floor Level", f"{floor_level:.2f} m above datum"])
            
            site_height = construction_data.get('SiteHeight')
            if isinstance(site_height, (int, float)):
                dimensions_data.append(["Site Height", f"{site_height:.2f} m"])
            
            dimensions_table = Table(dimensions_data, colWidths=self.table_widths['two_col'])
            dimensions_table.setStyle(self.table_styles['standard'])
            elements.append(dimensions_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # STRUCTURAL FEATURES
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Structural Features", self.styles['SubSectionHeader']))
            
            features_data = [["Feature", "Present"]]
            
            # Basement presence
            basement = construction_data.get('BasementPresent')
            if basement is not None:
                features_data.append(["Basement", self._format_value(basement)])
            
            # Construction year (from construction context)
            construction_year = construction_data.get('ConstructionYear')
            if construction_year:
                features_data.append(["Construction Year", str(construction_year)])
            
            features_table = Table(features_data, colWidths=self.table_widths['two_col'])
            features_table.setStyle(self.table_styles['standard'])
            elements.append(features_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # CONSTRUCTION ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Construction Analysis", self.styles['SubSectionHeader']))
            
            # Analyze construction type for risk assessment
            analysis_data = [["Analysis Factor", "Assessment"]]
            
            construction_type = construction_data.get('ConstructionType', '').lower()
            
            # Construction type risk assessment
            if 'timber' in construction_type:
                construction_risk = "Medium - Fire and moisture considerations"
                maintenance_note = "Regular inspection for rot and pest damage"
            elif 'steel' in construction_type:
                construction_risk = "Low - Durable construction method"
                maintenance_note = "Monitor for corrosion in exposed areas"
            elif 'concrete' in construction_type:
                construction_risk = "Low - Robust construction method"
                maintenance_note = "Check for concrete carbonation over time"
            elif 'brick' in construction_type or 'masonry' in construction_type:
                construction_risk = "Low - Traditional solid construction"
                maintenance_note = "Monitor pointing and structural movement"
            else:
                construction_risk = "Assessment required - Unknown construction type"
                maintenance_note = "Professional structural survey recommended"
            
            analysis_data.append(["Construction Risk Level", construction_risk])
            analysis_data.append(["Maintenance Considerations", maintenance_note])
            
            # Foundation type analysis
            foundation_type = construction_data.get('FoundationType', '').lower()
            if 'raft' in foundation_type:
                foundation_note = "Suitable for variable ground conditions"
            elif 'pile' in foundation_type:
                foundation_note = "Deep foundations - suitable for poor ground"
            elif 'strip' in foundation_type:
                foundation_note = "Traditional foundations - suitable for stable ground"
            elif 'pad' in foundation_type:
                foundation_note = "Individual footings - economical for light loads"
            else:
                foundation_note = "Foundation type assessment may be required"
            
            analysis_data.append(["Foundation Suitability", foundation_note])
            
            # Height analysis
            if isinstance(property_height, (int, float)):
                if property_height > 15:
                    height_note = "Tall structure - enhanced fire safety considerations"
                elif property_height > 10:
                    height_note = "Medium height - standard building regulations apply"
                else:
                    height_note = "Standard height - typical residential scale"
                
                analysis_data.append(["Height Classification", height_note])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating construction details: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements