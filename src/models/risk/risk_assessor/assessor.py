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

"""RiskAssessor class — utility class for risk assessment calculations."""

from typing import Any, Dict, Optional

from .flood import (FLOOD_DEPTH_THRESHOLDS, assess_flood_risk_level,
                    assess_property_vulnerability, _generate_recommendations)
from .ltv import (LTV_RISK_THRESHOLDS, assess_ltv_risk_level,
                  calculate_combined_risk_score)
from .finance import (calculate_value_at_risk, assess_gauge_reliability,
                      calculate_distance_risk_factor, calculate_insurance_premium_factor)


class RiskAssessor:
    """Utility class for risk assessment calculations."""

    FLOOD_DEPTH_THRESHOLDS = FLOOD_DEPTH_THRESHOLDS
    LTV_RISK_THRESHOLDS = LTV_RISK_THRESHOLDS

    @classmethod
    def assess_flood_risk_level(cls, flood_depth: float) -> str:
        return assess_flood_risk_level(flood_depth)

    @classmethod
    def assess_ltv_risk_level(cls, ltv_ratio: float) -> str:
        return assess_ltv_risk_level(ltv_ratio)

    @classmethod
    def calculate_combined_risk_score(cls, flood_risk_level: str, ltv_ratio: float,
                                      property_age: Optional[int] = None,
                                      construction_type: Optional[str] = None) -> float:
        return calculate_combined_risk_score(flood_risk_level, ltv_ratio, property_age, construction_type)

    @classmethod
    def assess_property_vulnerability(cls, ground_elevation: float, flood_level: float,
                                      distance_to_water: Optional[float] = None) -> Dict[str, Any]:
        return assess_property_vulnerability(ground_elevation, flood_level, distance_to_water)

    @classmethod
    def calculate_value_at_risk(cls, property_value: float, risk_level: str,
                                flood_depth: Optional[float] = None) -> float:
        return calculate_value_at_risk(property_value, risk_level, flood_depth)

    @classmethod
    def assess_gauge_reliability(cls, operational_status: str,
                                 last_maintenance: Optional[str] = None,
                                 data_frequency: Optional[str] = None) -> Dict[str, Any]:
        return assess_gauge_reliability(operational_status, last_maintenance, data_frequency)

    @classmethod
    def calculate_distance_risk_factor(cls, distance_km: float) -> float:
        return calculate_distance_risk_factor(distance_km)

    @classmethod
    def calculate_insurance_premium_factor(cls, risk_level: str, property_value: float,
                                           flood_depth: Optional[float] = None) -> float:
        return calculate_insurance_premium_factor(risk_level, property_value, flood_depth)

    @classmethod
    def _generate_recommendations(cls, flood_depth: float, risk_level: str) -> list:
        return _generate_recommendations(flood_depth, risk_level)
