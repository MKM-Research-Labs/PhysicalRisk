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

"""OED code lookup tables (CDM value -> OED code)."""

from typing import Dict

# ---------------------------------------------------------------------------
# Lookup tables  (CDM value → OED integer code)
# ---------------------------------------------------------------------------

# OED OccupancyCode — OED v5 Chapter 3 Appendix A
# CDM OccupancyType / PropertyResi → OED 4-digit code
_OCCUPANCY_CODE: Dict[str, int] = {
    # Residential
    "Residential owner-occupied":     1000,
    "Residential rented":             1000,
    "Residential social":             1000,
    "Detached house":                 1050,
    "Semi-detached house":            1050,
    "Terraced house":                 1050,
    "Bungalow":                       1050,
    "Flat":                           1100,
    "Maisonette":                     1100,
    "Apartment":                      1100,
    "Studio":                         1100,
    # Commercial
    "Commercial":                     1150,
    "Office":                         1160,
    "Retail":                         1170,
    "Restaurant":                     1180,
    "Hotel":                          1190,
    # Industrial
    "Industrial":                     1200,
    "Warehouse":                      1210,
    "Factory":                        1210,
    "Mixed Use":                      1300,
}

# OED ConstructionCode — Chapter 3 Appendix B
# CDM ConstructionType → OED code
_CONSTRUCTION_CODE: Dict[str, int] = {
    "Brick":                     5000,
    "Stone":                     5010,
    "Concrete":                  5050,
    "Reinforced Concrete":       5055,
    "Timber frame":              5100,
    "Steel frame":               5150,
    "Steel":                     5150,
    "Masonry":                   5010,
    "Mixed":                     5999,
    "Other":                     5999,
}

# OED FoundationType — Chapter 3 Appendix C
# CDM FoundationType → OED code
_FOUNDATION_CODE: Dict[str, int] = {
    "Strip foundations":         1,
    "Pad foundations":           2,
    "Raft foundations":          3,
    "Pile foundations":          4,
    "Deep foundations":          4,
    "Basement":                  5,
    "Slab on grade":             6,
    "Unknown":                   99,
    "Other":                     99,
}

# OED BuildingCondition — CDM PropertyCondition → OED code
# OED: 1=Good, 2=Average, 3=Poor
_BUILDING_CONDITION: Dict[str, int] = {
    "Excellent":   1,
    "Good":        1,
    "Average":     2,
    "Fair":        2,
    "Poor":        3,
    "Very poor":   3,
}

# OED TerrainRoughness — CDM UrbanRuralClassification → OED
# OED: 1=Open, 2=Rural, 3=Suburban, 4=Urban, 5=Dense urban
_TERRAIN_ROUGHNESS: Dict[str, int] = {
    "Rural":         2,
    "Semi-rural":    2,
    "Suburban":      3,
    "Urban":         4,
    "Dense urban":   5,
}

# OED SoilType — CDM SoilType → OED (NEHRP site class)
# OED: 1=Rock(A/B), 2=Stiff soil(C), 3=Soft soil(D), 4=Very soft(E), 5=Mixed
_SOIL_TYPE: Dict[str, int] = {
    "Rock":          1,
    "Chalk":         1,
    "Hard":          1,
    "Gravel":        2,
    "Clay":          3,
    "Sand":          3,
    "Alluvial":      3,
    "Peat":          4,
    "Soft":          4,
    "Mixed":         5,
}

# OED SoilLiquefiable — CDM LiquefactionMitigationProvided inverse proxy
# "Not assessed" / absent → 1 (unknown); "Partial"/"Verified" → 0 (no/mitigated)
_SOIL_LIQUEFIABLE: Dict[str, int] = {
    "Not assessed":  1,
    "Partial":       0,
    "Verified":      0,
    "Enhanced":      0,
}

# OED ServiceEquipmentProtection — CDM ElectricalSystemsAboveFlood proxy
_SEP: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}

# OED PerilsCovered codes (bitfield-style, represented as OED string)
# Derived from CDM HazardProfile classes: None/Low/Medium/High/Extreme
_HAZARD_OASIS_CODE: Dict[str, str] = {
    "FloodHazardClass":   "WF",   # Windstorm Flood
    "WindHazardClass":    "WSS",  # Windstorm Straight-line
    "SeismicHazardClass": "QEQ",  # Earthquake
    "FireHazardClass":    "BFR",  # Bushfire
}
_HAZARD_ACTIVE_CLASSES = {"Medium", "High", "Extreme", "Very High"}

# OED RoofAnchorage proxy from roof-related CDM booleans
# "RoofRatedForDesignWind" / "RoofEdgeDetailWindResistant"
_ROOF_ANCHORAGE: Dict[str, int] = {
    "Not assessed":  1,
    "Partial":       2,
    "Verified":      3,
    "Enhanced":      3,
}

# OED WindowProtection proxy from OpeningsWindResistant
_WINDOW_PROTECTION: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}

# OED CladdingType proxy from CladdingRatedForDesignWind
_CLADDING: Dict[str, int] = {
    "Not assessed":  0,
    "Partial":       1,
    "Verified":      2,
    "Enhanced":      2,
}
