# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Mekong (Cambodia / lower Mekong) rand-generation profile — catchment data.

The shared property/commercial generators read these via
``port.rand.profiles.active_profile()``. Generation LOGIC is shared; only the
values that genuinely differ by catchment live here.

Seed values are defensible placeholders for a Phnom Penh / lower-Mekong
floodplain model; refine against real calibration data when available.
"""

# Seismic — Cambodia is low-hazard intraplate (no major active faults near the
# lower Mekong): low PGA, None/Low-weighted hazard class.
SEISMIC_PGA_RANGE = (0.02, 0.10)
SEISMIC_HAZARD_CLASS_WEIGHTS = [0.55, 0.35, 0.08, 0.02, 0.00]

# BRI regime: the lower Mekong is strongly fluvial-flood / monsoon exposed
# (annual flood pulse, Tonle Sap reversal), so resilience scoring is published
# and the numeric BRI scores are computed.
PUBLISH_BRI_LETTER_RATINGS = True
BRI_SCORES_ENABLED = True


# ---------------------------------------------------------------------------
# Commercial archetype tables (read by the shared commercial generators).
# Mekong = SE-Asia (Phnom Penh-style) market; USD-denominated stock; the SE-Asia
# commercial BRI flood/flash coding applies.
# ---------------------------------------------------------------------------

COMMERCIAL_BRI_ENABLED = True

COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]

# (min_sqm, max_sqm) — gross internal area. Phnom Penh stock is generally
# smaller-footprint than Hanoi.
COMMERCIAL_TYPE_AREA_RANGE = {
    "Office": (5000, 28000),
    "MultiFamily": (12000, 38000),
    "Hotel": (8000, 40000),
    "Retail": (300, 5000),
    "MixedUse": (10000, 42000),
}

# USD/sqm capital value — broad, synthetic ranges for a Phnom Penh-style model.
COMMERCIAL_TYPE_VALUE_PER_SQM = {
    "Office": (600, 1400),
    "MultiFamily": (550, 1250),
    "Hotel": (700, 1600),
    "Retail": (800, 2000),
    "MixedUse": (650, 1500),
}

COMMERCIAL_TYPE_USE_CLASS = {
    "Office": "Office",
    "MultiFamily": "ResidentialIncome",
    "Hotel": "Hospitality",
    "Retail": "Retail",
    "MixedUse": "MixedUse",
}

COMMERCIAL_TYPE_BUSINESS_RATES = {
    "Office": "Office",
    "MultiFamily": "ResidentialIncome",
    "Hotel": "Hospitality",
    "Retail": "Retail",
    "MixedUse": "MixedUse",
}

COMMERCIAL_TYPE_STOREYS = {
    "Office": (5, 22),
    "MultiFamily": (8, 30),
    "Hotel": (5, 22),
    "Retail": (1, 5),
    "MixedUse": (5, 26),
}

COMMERCIAL_TYPE_TOTAL_UNITS = {
    "Office": (1, 8),
    "MultiFamily": (30, 260),
    "Hotel": (40, 300),
    "Retail": (1, 18),
    "MixedUse": (5, 160),
}

COMMERCIAL_TYPE_PARKING_SPACES = {
    "Office": (15, 160),
    "MultiFamily": (10, 110),
    "Hotel": (10, 130),
    "Retail": (5, 110),
    "MixedUse": (10, 150),
}

COMMERCIAL_TYPE_LOADING_BAYS = {
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

COMMERCIAL_ANCHOR_TENANT_POOL = {
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

# (cutoff_year_exclusive, label); final entry has cutoff None (open-ended).
# Cambodia's commercial stock is overwhelmingly post-1990 (post-conflict).
COMMERCIAL_PERIOD_BUCKETS = [
    (1990, "Pre-1990"),
    (2000, "1990-1999"),
    (2010, "2000-2009"),
    (2018, "2010-2017"),
    (None, "2018-Present"),
]

# Per-type weighted construction-year bands (end None -> current year - 1).
COMMERCIAL_CONSTRUCTION_YEAR_BANDS = {
    "Office":      [((2000, 2009), 0.20), ((2010, 2017), 0.45), ((2018, None), 0.35)],
    "MultiFamily": [((2000, 2009), 0.15), ((2010, 2017), 0.40), ((2018, None), 0.45)],
    "Hotel":       [((2000, 2009), 0.15), ((2010, 2017), 0.40), ((2018, None), 0.45)],
    "Retail":      [((1995, 2009), 0.25), ((2010, 2017), 0.40), ((2018, None), 0.35)],
    "MixedUse":    [((2005, 2012), 0.25), ((2013, 2019), 0.45), ((2020, None), 0.30)],
}
# (min_year, max_year) fallback for unlisted types; max None -> current year - 1.
COMMERCIAL_CONSTRUCTION_YEAR_RANGE = (2000, None)
