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

"""Flatten PropertyHeader.RiskAssessment (hazard/exposure facts)."""


def flatten_risk_assessment(prop: dict, default_elevation: float) -> dict:
    """Return flat snake_case keys for PropertyHeader.RiskAssessment.

    GroundLevelMeters falls back to ``default_elevation`` when absent; the
    ``elevation`` alias mirrors the same value for flood-model compatibility.
    """
    risk = prop.get("PropertyHeader", {}).get("RiskAssessment", {})

    ground_level = risk.get("GroundLevelMeters")
    if ground_level is None:
        ground_level = default_elevation

    return {
        "flood_zone":          risk.get("EAFloodZone"),
        "overall_flood_risk":  risk.get("OverallFloodRisk"),
        "flood_risk_type":     risk.get("FloodRiskType"),
        "ground_level_meters": ground_level,
        "elevation":           ground_level,
        "river_distance":      risk.get("RiverDistanceMeters"),
        "base_flood_elevation_m": risk.get("BaseFloodElevationMeters"),
        "vertical_datum":          risk.get("VerticalDatum"),
        "soil_vs30_mps":           risk.get("SoilVs30Mps"),
        "flood_debris_present":    risk.get("FloodDebrisPresent"),
    }
