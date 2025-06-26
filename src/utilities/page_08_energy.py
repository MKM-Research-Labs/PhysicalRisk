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

# src/utilities/page_08_energy.py

"""
Page 8: Energy Performance
Handles energy efficiency, usage patterns, and environmental impact.
"""

from typing import Dict, Any, List
from reportlab.platypus import Paragraph, Spacer, Table
from .base_page import BasePage


class EnergyPage(BasePage):
    """Generates energy performance page."""
    
    def generate_elements(self, property_data: Dict[str, Any], 
                         mortgage_data: Dict[str, Any] = None) -> List:
        """Generate energy performance page elements."""
        elements = []
        
        try:
            elements.append(Paragraph("Energy Performance", self.styles['SectionHeader']))
            
            energy_data = property_data.get('EnergyPerformance', {})
            
            if not energy_data:
                elements.append(Paragraph("No energy performance data available.", self.styles['Normal']))
                return elements
            
            # ENERGY RATINGS
            ratings = energy_data.get('Ratings', {})
            if ratings:
                elements.append(Paragraph("Energy Ratings", self.styles['SubSectionHeader']))
                
                ratings_data = [["Rating Type", "Rating"]]
                for key, value in ratings.items():
                    if value is not None:
                        ratings_data.append([self._format_field_name(key), self._format_value(value)])
                
                ratings_table = Table(ratings_data, colWidths=self.table_widths['two_col'])
                ratings_table.setStyle(self.table_styles['energy'])
                elements.append(ratings_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ENERGY USAGE
            energy_usage = energy_data.get('EnergyUsage', {})
            if energy_usage:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Energy Consumption", self.styles['SubSectionHeader']))
                
                usage_data = [["Energy Metric", "Annual Consumption"]]
                
                # Key energy metrics
                annual_energy = energy_usage.get('AnnualEnergyKwh')
                if isinstance(annual_energy, (int, float)):
                    usage_data.append(["Total Energy Consumption", f"{annual_energy:,.0f} kWh"])
                
                grid_electricity = energy_usage.get('GridElectricityKwh')
                if isinstance(grid_electricity, (int, float)):
                    usage_data.append(["Grid Electricity", f"{grid_electricity:,.0f} kWh"])
                
                gas_usage = energy_usage.get('GasUsageKwh')
                if isinstance(gas_usage, (int, float)):
                    usage_data.append(["Gas Usage", f"{gas_usage:,.0f} kWh"])
                
                solar_generation = energy_usage.get('SolarGenerationKwh')
                if isinstance(solar_generation, (int, float)):
                    usage_data.append(["Solar Generation", f"{solar_generation:,.0f} kWh"])
                
                # Carbon emissions
                annual_carbon = energy_usage.get('AnnualCarbonKgCO2e')
                if isinstance(annual_carbon, (int, float)):
                    usage_data.append(["Carbon Emissions", f"{annual_carbon:,.1f} kg CO2e"])
                
                # Energy costs
                annual_bill = energy_usage.get('AnnualEnergyBill')
                if isinstance(annual_bill, (int, float)):
                    usage_data.append(["Annual Energy Bill", self._format_currency(annual_bill)])
                
                usage_table = Table(usage_data, colWidths=self.table_widths['two_col'])
                usage_table.setStyle(self.table_styles['energy'])
                elements.append(usage_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # BUILDING FABRIC
            building_fabric = energy_data.get('BuildingFabric', {})
            if building_fabric:
                elements.append(Spacer(1, self.spacing['minor_section']))
                elements.append(Paragraph("Building Fabric & Systems", self.styles['SubSectionHeader']))
                
                fabric_data = [["Building Element", "Specification"]]
                
                # Insulation
                loft_insulation = building_fabric.get('LoftInsulationMm')
                if isinstance(loft_insulation, (int, float)):
                    fabric_data.append(["Loft Insulation", f"{loft_insulation}mm"])
                
                # Performance scores
                thermal_bridge = building_fabric.get('ThermalBridgeScore')
                if isinstance(thermal_bridge, (int, float)):
                    fabric_data.append(["Thermal Bridge Score", f"{thermal_bridge:.2f}"])
                
                air_tightness = building_fabric.get('AirTightnessScore')
                if isinstance(air_tightness, (int, float)):
                    fabric_data.append(["Air Tightness Score", f"{air_tightness:.1f}"])
                
                # Building systems
                heating_system = building_fabric.get('HeatingSystem')
                if heating_system:
                    fabric_data.append(["Heating System", heating_system])
                
                water_heating = building_fabric.get('WaterHeating')
                if water_heating:
                    fabric_data.append(["Water Heating", water_heating])
                
                # Windows and doors
                glazing_type = building_fabric.get('GlazingType')
                if glazing_type:
                    fabric_data.append(["Glazing Type", glazing_type])
                
                fabric_table = Table(fabric_data, colWidths=self.table_widths['two_col'])
                fabric_table.setStyle(self.table_styles['energy'])
                elements.append(fabric_table)
                elements.append(Spacer(1, self.spacing['table_bottom']))
            
            # ENERGY EFFICIENCY ANALYSIS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Energy Efficiency Analysis", self.styles['SubSectionHeader']))
            
            analysis_data = [["Analysis Factor", "Assessment"]]
            
            # EPC rating analysis
            epc_rating = ratings.get('EPCRating', '') if ratings else ''
            if epc_rating:
                epc_analysis = self._analyze_epc_rating(epc_rating)
                analysis_data.append(["EPC Performance", epc_analysis])
            
            # Energy intensity analysis
            if isinstance(annual_energy, (int, float)):
                # Get property area for intensity calculation
                header_data = property_data.get('PropertyHeader', {})
                attributes_data = header_data.get('PropertyAttributes', {})
                area = attributes_data.get('PropertyAreaSqm')
                
                if isinstance(area, (int, float)) and area > 0:
                    energy_intensity = annual_energy / area
                    analysis_data.append(["Energy Intensity", f"{energy_intensity:.0f} kWh/sqm/year"])
                    
                    # Benchmark energy intensity
                    if energy_intensity > 200:
                        intensity_rating = "High - Above average consumption"
                    elif energy_intensity > 150:
                        intensity_rating = "Medium-High - Moderate consumption"
                    elif energy_intensity > 100:
                        intensity_rating = "Average - Typical consumption"
                    elif energy_intensity > 50:
                        intensity_rating = "Good - Below average consumption"
                    else:
                        intensity_rating = "Excellent - Very low consumption"
                    
                    analysis_data.append(["Intensity Rating", intensity_rating])
            
            # Carbon intensity analysis
            if isinstance(annual_carbon, (int, float)) and isinstance(area, (int, float)) and area > 0:
                carbon_intensity = annual_carbon / area
                analysis_data.append(["Carbon Intensity", f"{carbon_intensity:.1f} kg CO2e/sqm/year"])
            
            analysis_table = Table(analysis_data, colWidths=self.table_widths['two_col'])
            analysis_table.setStyle(self.table_styles['standard'])
            elements.append(analysis_table)
            
        except Exception as e:
            elements.append(Paragraph(
                f"Error generating energy performance: {str(e)}", 
                self.styles['Normal']
            ))
        
        return elements
    
    def _analyze_epc_rating(self, rating: str) -> str:
        """Analyze EPC rating and provide assessment."""
        rating_analysis = {
            'A': 'Excellent - Very energy efficient',
            'B': 'Good - Energy efficient',
            'C': 'Fairly good - Reasonably efficient',
            'D': 'Average - Some improvements possible',
            'E': 'Below average - Improvements recommended',
            'F': 'Poor - Significant improvements needed',
            'G': 'Very poor - Major improvements required'
        }
        return rating_analysis.get(rating.upper(), f'Unknown rating: {rating}')