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

"""Render the EnergyPerformance section of an asset.

EnergyPerformance has three sub-sections in the CDM:
``Ratings``, ``EnergyUsage`` and ``BuildingFabric``.
"""

from typing import Any, Dict, List

from reportlab.platypus import Paragraph

from ._helpers import auto_rows, section_block

_RATINGS_FIELDS = [
    ("EPCRating",      "EPC Rating"),
    ("CarbonRating",   "Carbon Rating"),
    ("EmissionsScore", "Emissions Score"),
]

_USAGE_FIELDS = [
    ("TariffType",          "Tariff Type"),
    ("HeatingSystem",       "Heating System"),
    ("RenewableSystem",     "Renewable System"),
    ("AnnualEnergyKwh",     "Annual Energy (kWh)"),
    ("GridElectricityKwh",  "Grid Electricity (kWh)"),
    ("GasUsageKwh",         "Gas Usage (kWh)"),
    ("SolarGenerationKwh",  "Solar Generation (kWh)"),
    ("AnnualCarbonKgCO2e",  "Annual Carbon (kg CO2e)"),
    ("AnnualEnergyBill",    "Annual Energy Bill"),
]

_FABRIC_FIELDS = [
    ("WallConstruction",   "Wall Construction"),
    ("CavityInsulation",   "Cavity Insulation"),
    ("ThermalBridgeScore", "Thermal Bridge Score"),
    ("LoftInsulationMm",   "Loft Insulation (mm)"),
    ("RoofType",           "Roof Type"),
    ("FloorConstruction",  "Floor Construction"),
    ("FloorInsulation",    "Floor Insulation"),
    ("HeatingSys",         "Heating Sys"),
    ("WaterHeating",       "Water Heating"),
    ("LightingType",       "Lighting Type"),
    ("AirTightnessScore",  "Air Tightness Score"),
    ("GlazingType",        "Glazing Type"),
    ("WindowFrameType",    "Window Frame Type"),
    ("DoorType",           "Door Type"),
    ("SmartMeterType",     "Smart Meter Type"),
]


def render_energy(energy: Dict[str, Any], page) -> List:
    """Build the energy performance tables."""
    elements: List = [
        Paragraph("Energy Performance", page.styles["SectionHeader"]),
    ]
    elements.extend(section_block(
        "Ratings",
        page,
        auto_rows(energy.get("Ratings", {}), _RATINGS_FIELDS),
        style="energy",
        header=("Rating", "Value"),
    ))
    elements.extend(section_block(
        "Energy Usage",
        page,
        auto_rows(energy.get("EnergyUsage", {}), _USAGE_FIELDS),
        style="energy",
        header=("Usage", "Value"),
    ))
    elements.extend(section_block(
        "Building Fabric",
        page,
        auto_rows(energy.get("BuildingFabric", {}), _FABRIC_FIELDS),
        style="energy",
        header=("Component", "Value"),
    ))
    return elements
