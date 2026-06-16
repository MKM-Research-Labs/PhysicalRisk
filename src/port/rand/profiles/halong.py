# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Halong (coastal Vietnam) rand-generation profile — catchment-specific data.

The shared property/commercial generators read these via
``port.rand.profiles.active_profile()``. Generation LOGIC is shared; only the
values that genuinely differ by catchment live here.
"""

# Seismic — Halong sits on the Red River Fault Zone, rated High by the
# MKM-SEIS-001 hazard table: higher PGA, Medium/High-weighted hazard class.
SEISMIC_PGA_RANGE = (0.12, 0.50)
SEISMIC_HAZARD_CLASS_WEIGHTS = [0.05, 0.15, 0.35, 0.30, 0.15]

# BRI regime: Halong publishes certified BRI letter ratings + numeric scores.
PUBLISH_BRI_LETTER_RATINGS = True
BRI_SCORES_ENABLED = True


# ---------------------------------------------------------------------------
# Commercial archetype tables (read by the shared commercial generators).
# Halong = SE-Asia (Hanoi-style) market values; USD; full commercial BRI coding.
# ---------------------------------------------------------------------------

# Halong commercial assets carry the BRI Water/Flash/Wind/Fire/Seismic coding.
COMMERCIAL_BRI_ENABLED = True

COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]

# (min_sqm, max_sqm) — gross internal area
COMMERCIAL_TYPE_AREA_RANGE = {
    "Office": (8000, 35000),
    "MultiFamily": (18000, 42000),
    "Hotel": (12000, 45000),
    "Retail": (300, 6000),
    "MixedUse": (15000, 50000),
}

# USD/sqm capital value — broad, synthetic ranges for a Hanoi-style model.
COMMERCIAL_TYPE_VALUE_PER_SQM = {
    "Office": (700, 1600),
    "MultiFamily": (650, 1400),
    "Hotel": (800, 1800),
    "Retail": (900, 2200),
    "MixedUse": (750, 1700),
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
    "Office": (6, 24),
    "MultiFamily": (12, 32),
    "Hotel": (6, 24),
    "Retail": (1, 5),
    "MixedUse": (5, 28),
}

COMMERCIAL_TYPE_TOTAL_UNITS = {
    "Office": (1, 8),
    "MultiFamily": (40, 300),
    "Hotel": (40, 320),
    "Retail": (1, 20),
    "MixedUse": (5, 180),
}

COMMERCIAL_TYPE_PARKING_SPACES = {
    "Office": (20, 180),
    "MultiFamily": (10, 120),
    "Hotel": (10, 140),
    "Retail": (5, 120),
    "MixedUse": (10, 160),
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
COMMERCIAL_PERIOD_BUCKETS = [
    (1980, "Pre-1980"),
    (1995, "1980-1994"),
    (2005, "1995-2004"),
    (2015, "2005-2014"),
    (None, "2015-Present"),
]

# Construction-year strategy. Hanoi's commercial stock is overwhelmingly
# post-Doi-Moi, so years are drawn from weighted per-type bands. Each band is
# ((start, end), weight); end None -> current year - 1 (open-ended). Types not
# listed fall back to a uniform draw over COMMERCIAL_CONSTRUCTION_YEAR_RANGE.
COMMERCIAL_CONSTRUCTION_YEAR_BANDS = {
    "Office":      [((1995, 2004), 0.15), ((2005, 2014), 0.45), ((2015, None), 0.40)],
    "MultiFamily": [((1995, 2004), 0.10), ((2005, 2014), 0.40), ((2015, None), 0.50)],
    "Hotel":       [((1995, 2004), 0.10), ((2005, 2014), 0.35), ((2015, None), 0.55)],
    "Retail":      [((1985, 1994), 0.15), ((1995, 2004), 0.25),
                    ((2005, 2014), 0.35), ((2015, None), 0.25)],
    "MixedUse":    [((2000, 2009), 0.20), ((2010, 2017), 0.45), ((2018, None), 0.35)],
}
# (min_year, max_year) fallback for unlisted types; max None -> current year - 1.
COMMERCIAL_CONSTRUCTION_YEAR_RANGE = (2005, None)
