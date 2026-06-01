# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Per-CommercialType parameter tables for the commercial generators.

Hanoi-oriented commercial archetype tables. The first 10-asset slice
still uses a fixed mix for repeatability, but the labels and tenant
pools are made neutral / Asia-facing rather than UK-specific.
"""

COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]

# (min_sqm, max_sqm) — gross internal area
TYPE_AREA_RANGE = {
    "Office": (8000, 35000),
    "MultiFamily": (18000, 42000),
    "Hotel": (12000, 45000),
    "Retail": (300, 6000),
    "MixedUse": (15000, 50000),
}

# USD/sqm capital value — broad, synthetic ranges for a Hanoi-style model.
TYPE_VALUE_PER_SQM = {
    "Office": (700, 1600),
    "MultiFamily": (650, 1400),
    "Hotel": (800, 1800),
    "Retail": (900, 2200),
    "MixedUse": (750, 1700),
}

# Keep field names for schema compatibility, but use neutral values.
TYPE_USE_CLASS = {
    "Office": "Office",
    "MultiFamily": "ResidentialIncome",
    "Hotel": "Hospitality",
    "Retail": "Retail",
    "MixedUse": "MixedUse",
}

TYPE_BUSINESS_RATES = {
    "Office": "Office",
    "MultiFamily": "ResidentialIncome",
    "Hotel": "Hospitality",
    "Retail": "Retail",
    "MixedUse": "MixedUse",
}

# (min_storeys, max_storeys)
TYPE_STOREYS = {
    "Office": (6, 24),
    "MultiFamily": (12, 32),
    "Hotel": (6, 24),
    "Retail": (1, 5),
    "MixedUse": (5, 28),
}

TYPE_TOTAL_UNITS = {
    "Office": (1, 8),
    "MultiFamily": (40, 300),
    "Hotel": (40, 320),
    "Retail": (1, 20),
    "MixedUse": (5, 180),
}

TYPE_PARKING_SPACES = {
    "Office": (20, 180),
    "MultiFamily": (10, 120),
    "Hotel": (10, 140),
    "Retail": (5, 120),
    "MixedUse": (10, 160),
}

TYPE_LOADING_BAYS = {
    "Office": (0, 2),
    "MultiFamily": (0, 1),
    "Hotel": (0, 3),
    "Retail": (0, 4),
    "MixedUse": (0, 4),
}

COMMERCIAL_CONSTRUCTION_TYPES = [
    "Concrete frame",
    "Reinforced concrete",
    "Steel frame",
    "Mixed construction",
]

ANCHOR_TENANT_POOL = {
    "Office": [
        "Multi-let",
        "Local company",
        "Technology tenant",
        "Financial services tenant",
        "Professional services tenant",
        "Government office",
        "Regional representative office",
        "Co-working operator",
    ],
    "MultiFamily": [
        "Multi-let",
        "Apartment rental",
        "Serviced apartment operator",
    ],
    "Hotel": [
        "Independent hotel",
        "Domestic hotel operator",
        "International hotel flag",
        "Business hotel operator",
        "Boutique hotel operator",
    ],
    "Retail": [
        "Multi-let",
        "Local retailer",
        "Convenience store",
        "Food and beverage tenant",
        "Pharmacy / health retailer",
        "Mini-mart operator",
    ],
    "MixedUse": [
        "Multi-let",
        "Podium retail + residential",
        "Podium retail + office",
        "Mixed local tenants",
    ],
}
