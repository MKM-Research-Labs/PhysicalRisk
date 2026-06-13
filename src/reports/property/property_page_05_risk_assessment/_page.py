# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

# src/utilities/page_05_risk_assessment.py

"""
Page 5: Risk Assessment
Handles comprehensive property risk analysis including flood, environmental, and location-based risks.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph, Spacer, Table

from ..property_page_00_base import PropertyBasePage
from ._helpers import _RiskHelpersMixin


class RiskAssessmentPage(_RiskHelpersMixin, PropertyBasePage):
    """Generates property risk assessment page."""

    def generate_elements(self, property_data: Dict[str, Any],
                         rloan_data: Dict[str, Any] = None) -> List:
        """Generate risk assessment page elements."""
        elements = []

        try:
            elements.append(Paragraph("Property Risk Assessment", self.styles['SectionHeader']))

            header_data = property_data.get('PropertyHeader', {})
            risk_data = header_data.get('RiskAssessment', {})
            hazard_profile = property_data.get('ProtectionMeasures', {}).get('HazardProfile', {})

            # FLOOD RISK ASSESSMENT
            elements.append(Paragraph("Flood Risk Analysis", self.styles['SubSectionHeader']))

            flood_data = [["Risk Factor", "Assessment"]]

            # Environment Agency flood zone
            ea_zone = risk_data.get('EAFloodZone')
            if ea_zone:
                flood_data.append(["EA Flood Zone", ea_zone])

                # Interpret flood zone
                zone_interpretation = self._interpret_flood_zone(ea_zone)
                flood_data.append(["Zone Risk Level", zone_interpretation])

            # Overall flood risk
            overall_risk = risk_data.get('OverallFloodRisk')
            if overall_risk:
                flood_data.append(["Overall Flood Risk", overall_risk])

            # Flood risk type
            risk_type = risk_data.get('FloodRiskType')
            if risk_type:
                flood_data.append(["Risk Type", risk_type])

            # Last flood date
            last_flood = risk_data.get('LastFloodDate')
            if last_flood:
                flood_data.append(["Last Flood Date", last_flood])

            # Flood geometry
            bfe = risk_data.get('BaseFloodElevationMeters')
            if isinstance(bfe, (int, float)):
                datum = risk_data.get('VerticalDatum', 'AOD')
                flood_data.append(["Base Flood Elevation", f"{bfe:.2f} m ({datum})"])

            debris = risk_data.get('FloodDebrisPresent')
            if debris is not None:
                flood_data.append(["Debris Risk in Catchment", "Yes" if debris else "No"])

            # Design return period from hazard profile
            design_return = hazard_profile.get('DesignFloodReturnYr')
            if design_return:
                flood_data.append(["Design Return Period", f"1-in-{design_return} year"])

            flood_table = Table(flood_data, colWidths=self.table_widths['two_col'])
            flood_table.setStyle(self.table_styles['risk'])
            elements.append(flood_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # ELEVATION AND WATER PROXIMITY
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Elevation & Water Proximity", self.styles['SubSectionHeader']))

            elevation_data = [["Geographic Factor", "Measurement"]]

            # Ground elevation
            ground_level = risk_data.get('GroundLevelMeters')
            if isinstance(ground_level, (int, float)):
                elevation_data.append(["Ground Elevation", f"{ground_level:.2f} m above sea level"])

                # Elevation risk assessment
                if ground_level < 5:
                    elevation_risk = "High risk - Very low elevation"
                elif ground_level < 10:
                    elevation_risk = "Medium risk - Low elevation"
                elif ground_level < 20:
                    elevation_risk = "Low-medium risk - Moderate elevation"
                else:
                    elevation_risk = "Low risk - Good elevation"

                elevation_data.append(["Elevation Risk", elevation_risk])

            # Distance to water bodies
            river_distance = risk_data.get('RiverDistanceMeters')
            if isinstance(river_distance, (int, float)):
                elevation_data.append(["River Distance", f"{river_distance:.0f} m"])

                if river_distance < 100:
                    river_risk = "High risk - Very close to river"
                elif river_distance < 500:
                    river_risk = "Medium risk - Close to river"
                elif river_distance < 1000:
                    river_risk = "Low-medium risk - Moderate distance"
                else:
                    river_risk = "Low risk - Good distance from river"

                elevation_data.append(["River Proximity Risk", river_risk])

            # Coastal distance
            coastal_distance = risk_data.get('CoastalDistanceMeters')
            if isinstance(coastal_distance, (int, float)):
                coastal_km = coastal_distance / 1000
                elevation_data.append(["Coastal Distance", f"{coastal_km:.1f} km"])

            # Lake distance
            lake_distance = risk_data.get('LakeDistanceMeters')
            if isinstance(lake_distance, (int, float)):
                elevation_data.append(["Lake Distance", f"{lake_distance:.0f} m"])

            # Canal distance
            canal_distance = risk_data.get('CanalDistanceMeters')
            if isinstance(canal_distance, (int, float)):
                elevation_data.append(["Canal Distance", f"{canal_distance:.0f} m"])

            elevation_table = Table(elevation_data, colWidths=self.table_widths['two_col'])
            elevation_table.setStyle(self.table_styles['standard'])
            elements.append(elevation_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # ENVIRONMENTAL FACTORS
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Environmental Risk Factors", self.styles['SubSectionHeader']))

            environmental_data = [["Environmental Factor", "Status"]]

            # Soil type
            soil_type = risk_data.get('SoilType')
            if soil_type:
                environmental_data.append(["Soil Type", soil_type])
                environmental_data.append(["Soil Risk Level", self._assess_soil_risk(soil_type)])

            vs30 = risk_data.get('SoilVs30Mps')
            if isinstance(vs30, (int, float)):
                site_class = self._vs30_site_class(vs30)
                environmental_data.append(["Shear Wave Velocity (Vs30)", f"{vs30:.0f} m/s — {site_class}"])

            # Wind design intensity from hazard profile
            wind_speed = hazard_profile.get('DesignWindSpeedKmh')
            if isinstance(wind_speed, (int, float)):
                environmental_data.append(["Design Wind Speed", f"{wind_speed:.0f} km/h"])

            seismic_pga = hazard_profile.get('DesignSeismicPGA')
            if isinstance(seismic_pga, (int, float)):
                environmental_data.append(["Design Seismic PGA", f"{seismic_pga:.3f} g"])

            environmental_table = Table(environmental_data, colWidths=self.table_widths['two_col'])
            environmental_table.setStyle(self.table_styles['standard'])
            elements.append(environmental_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # FLOOD DEFENCES
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Flood Defence Systems", self.styles['SubSectionHeader']))

            defence_data = [["Defence System", "Status"]]

            # Government defence scheme
            govt_defence = risk_data.get('GovernmentalDefenceScheme')
            if govt_defence is not None:
                defence_data.append(["Government Defence Scheme", self._format_value(govt_defence)])

                if govt_defence:
                    defence_data.append(["Defence Benefit", "Reduced flood risk from scheme"])
                else:
                    defence_data.append(["Defence Status", "No formal defence scheme"])

            defence_table = Table(defence_data, colWidths=self.table_widths['two_col'])
            defence_table.setStyle(self.table_styles['protection'])
            elements.append(defence_table)
            elements.append(Spacer(1, self.spacing['table_bottom']))

            # OVERALL RISK SUMMARY
            elements.append(Spacer(1, self.spacing['minor_section']))
            elements.append(Paragraph("Risk Summary", self.styles['SubSectionHeader']))

            # Calculate overall risk score
            risk_score = self._calculate_risk_score(risk_data)

            summary_data = [["Risk Category", "Assessment"]]
            summary_data.append(["Overall Risk Level", risk_score['level']])
            summary_data.append(["Risk Score", f"{risk_score['score']}/10"])
            summary_data.append(["Primary Risk Factors", risk_score['primary_factors']])
            summary_data.append(["Recommended Actions", risk_score['recommendations']])

            summary_table = Table(summary_data, colWidths=self.table_widths['two_col'])
            summary_table.setStyle(self.table_styles['risk'])
            elements.append(summary_table)

        except Exception as e:
            elements.append(Paragraph(
                f"Error generating risk assessment: {str(e)}",
                self.styles['Normal']
            ))

        return elements
