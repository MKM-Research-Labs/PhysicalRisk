# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
EnergyPerformance — EPC ratings, energy usage, and building fabric.

Not part of the revised Property CDM proposal (BRI is silent on energy),
but kept here because:

  - port.rand.thames.property.property_random.generators contains lambda
    generators for every field below;
  - src/reports/property/property_page_08_energy.py reads
    EnergyPerformance.Ratings, EnergyPerformance.EnergyUsage,
    EnergyPerformance.BuildingFabric;
  - src/reports/property/property_page_15_data_summary.py treats
    EnergyPerformance as a top-level section alongside PropertyHeader.

Top-level placement (peer of PropertyHeader/ProtectionMeasures) matches the
shape the existing reports expect.
"""

ENERGY_PERFORMANCE_SCHEMA = {
    "Ratings": {
        "EPCRating": {
            "type": "menu",
            "options": ["A", "B", "C", "D", "E", "F", "G"],
            "description": "Energy Performance Certificate rating"
        },
        "CarbonRating": {
            "type": "menu",
            "options": ["A+", "A", "B", "C", "D", "E", "F"],
            "description": "Carbon emissions rating"
        },
        "EmissionsScore": {
            "type": "menu",
            "options": ["Excellent", "Good", "Fair", "Poor", "Very poor"],
            "description": "Qualitative emissions score"
        }
    },
    "EnergyUsage": {
        "TariffType": {
            "type": "menu",
            "options": ["Wood Fire", "Gas", "Electricity", "Both"],
            "description": "Primary energy tariff type"
        },
        "HeatingSystem": {
            "type": "menu",
            "options": [
                "Gas central heating", "Electric heating", "Heat pump",
                "Oil heating", "Other",
            ],
            "description": "Primary heating system (usage classification)"
        },
        "RenewableSystem": {
            "type": "menu",
            "options": ["None", "Solar PV", "Solar thermal", "Heat pump", "Multiple"],
            "description": "Installed on-site renewable energy systems"
        },
        "AnnualEnergyKwh": {
            "type": "decimal",
            "description": "Total annual energy consumption (kWh)"
        },
        "GridElectricityKwh": {
            "type": "decimal",
            "description": "Annual grid electricity consumption (kWh)"
        },
        "GasUsageKwh": {
            "type": "decimal",
            "description": "Annual gas consumption (kWh)"
        },
        "SolarGenerationKwh": {
            "type": "decimal",
            "description": "Annual on-site solar generation (kWh)"
        },
        "AnnualCarbonKgCO2e": {
            "type": "decimal",
            "description": "Annual carbon emissions in kg CO2-equivalent"
        },
        "AnnualEnergyBill": {
            "type": "decimal",
            "description": "Estimated annual energy bill in local currency"
        }
    },
    "BuildingFabric": {
        "WallConstruction": {
            "type": "menu",
            "options": [
                "Solid brick", "Cavity brick", "Timber frame",
                "Modern methods of construction", "Stone", "System build",
                "Concrete",
            ],
            "description": "Wall construction type"
        },
        "CavityInsulation": {
            "type": "boolean",
            "description": "Cavity-wall insulation installed"
        },
        "ThermalBridgeScore": {
            "type": "decimal",
            "description": "Thermal bridge severity score (lower is better)"
        },
        "LoftInsulationMm": {
            "type": "integer",
            "description": "Loft insulation thickness in millimetres"
        },
        "RoofType": {
            "type": "menu",
            "options": [
                "Flat roof", "Pitched with tiles", "Pitched with slate",
                "Pitched with other", "Mansard", "Barrel vault",
                "Green roof", "Mixed",
            ],
            "description": "Roof type"
        },
        "FloorConstruction": {
            "type": "menu",
            "options": [
                "Solid concrete", "Suspended timber", "Suspended concrete",
                "Beam and block", "Mixed construction",
            ],
            "description": "Ground floor construction type"
        },
        "FloorInsulation": {
            "type": "boolean",
            "description": "Ground floor insulation installed"
        },
        "HeatingSys": {
            "type": "menu",
            "options": [
                "Combi boiler", "System boiler", "Regular boiler",
                "Electric storage heaters", "Air source heat pump",
                "Ground source heat pump", "District heating", "Biomass boiler",
                "Direct electric", "Hybrid system",
            ],
            "description": "Detailed heating system specification"
        },
        "WaterHeating": {
            "type": "menu",
            "options": [
                "Gas combi", "Gas system with cylinder", "Electric immersion",
                "Heat pump", "Solar thermal", "District heating",
                "Instant electric", "Gas multipoint",
            ],
            "description": "Water-heating system"
        },
        "LightingType": {
            "type": "menu",
            "options": [
                "LED", "Compact fluorescent", "Halogen", "Mixed types",
                "Traditional", "Smart LED",
            ],
            "description": "Primary lighting technology"
        },
        "AirTightnessScore": {
            "type": "decimal",
            "description": "Air-tightness test result (m³/h/m² at 50 Pa)"
        },
        "GlazingType": {
            "type": "menu",
            "options": [
                "Single", "Double", "Triple", "Secondary glazing",
                "Mixed types", "Low-E coated", "Solar control",
            ],
            "description": "Glazing type"
        },
        "WindowFrameType": {
            "type": "menu",
            "options": [
                "uPVC", "Timber", "Aluminum", "Composite", "Steel",
                "Mixed materials",
            ],
            "description": "Window frame material"
        },
        "DoorType": {
            "type": "menu",
            "options": [
                "uPVC", "Timber", "Composite", "Aluminum", "Steel",
                "Mixed materials", "Traditional",
            ],
            "description": "External door material"
        },
        "SmartMeterType": {
            "type": "menu",
            "options": [
                "None", "Basic meter", "Smart meter",
                "Smart meter with export capability", "Smart prepayment",
            ],
            "description": "Smart-meter installation"
        }
    }
}
