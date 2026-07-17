# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Risk-scoring and interpretation helpers for the risk assessment page."""

from typing import Any, Dict


class _RiskHelpersMixin:
    """Pure-logic helpers for risk interpretation and scoring."""

    def _interpret_flood_zone(self, zone: str) -> str:
        """Interpret EA flood zone codes."""
        zone_interpretations = {
            'Zone 1': 'Low risk - Less than 1 in 1000 annual probability',
            'Zone 2': 'Medium risk - 1 in 1000 to 1 in 100 annual probability',
            'Zone 3a': 'High risk - Greater than 1 in 100 annual probability',
            'Zone 3b': 'Functional floodplain - Used for flood storage'
        }
        return zone_interpretations.get(zone, f'Unknown zone: {zone}')

    def _vs30_site_class(self, vs30: float) -> str:
        """Map Vs30 (m/s) to NEHRP/OED site class label."""
        if vs30 >= 760:
            return "Rock (Site Class A/B)"
        elif vs30 >= 360:
            return "Stiff soil (Site Class C)"
        elif vs30 >= 180:
            return "Soft soil (Site Class D)"
        else:
            return "Very soft soil (Site Class E)"

    def _assess_soil_risk(self, soil_type: str) -> str:
        """Assess risk based on soil type."""
        soil_type_lower = soil_type.lower()

        if 'peat' in soil_type_lower:
            return 'High risk - Peat soils can shrink and subside'
        elif 'clay' in soil_type_lower:
            return 'Medium-high risk - Clay can shrink and swell'
        elif 'sand' in soil_type_lower:
            return 'Medium risk - Sandy soils drain well but can be unstable'
        elif 'rock' in soil_type_lower or 'bedrock' in soil_type_lower:
            return 'Low risk - Stable foundation conditions'
        else:
            return f'Assessment required - {soil_type} characteristics need evaluation'

    def _calculate_risk_score(self, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall property risk score."""
        score = 0
        risk_factors = []

        # Flood risk scoring
        overall_flood = risk_data.get('OverallFloodRisk', '').lower()
        if 'very high' in overall_flood:
            score += 4
            risk_factors.append('Very High Flood Risk')
        elif 'high' in overall_flood:
            score += 3
            risk_factors.append('High Flood Risk')
        elif 'medium' in overall_flood:
            score += 2
            risk_factors.append('Medium Flood Risk')
        elif 'low' in overall_flood:
            score += 1

        # Elevation scoring
        ground_level = risk_data.get('GroundLevelMeters')
        if isinstance(ground_level, (int, float)):
            if ground_level < 5:
                score += 3
                risk_factors.append('Very Low Elevation')
            elif ground_level < 10:
                score += 2
                risk_factors.append('Low Elevation')
            elif ground_level < 20:
                score += 1

        # River proximity scoring
        river_distance = risk_data.get('RiverDistanceMeters')
        if isinstance(river_distance, (int, float)):
            if river_distance < 100:
                score += 2
                risk_factors.append('Very Close to River')
            elif river_distance < 500:
                score += 1
                risk_factors.append('Close to River')

        # Soil type scoring
        soil_type = risk_data.get('SoilType', '').lower()
        if 'peat' in soil_type:
            score += 2
            risk_factors.append('Peat Soil')
        elif 'clay' in soil_type:
            score += 1
            risk_factors.append('Clay Soil')

        # Determine risk level
        if score >= 8:
            level = 'Very High Risk'
            recommendations = 'Comprehensive flood protection and insurance essential'
        elif score >= 6:
            level = 'High Risk'
            recommendations = 'Flood protection measures strongly recommended'
        elif score >= 4:
            level = 'Medium Risk'
            recommendations = 'Consider flood protection measures'
        elif score >= 2:
            level = 'Low-Medium Risk'
            recommendations = 'Standard precautions adequate'
        else:
            level = 'Low Risk'
            recommendations = 'Minimal additional protection required'

        return {
            'score': score,
            'level': level,
            'primary_factors': ', '.join(risk_factors) if risk_factors else 'No major risk factors identified',
            'recommendations': recommendations
        }
