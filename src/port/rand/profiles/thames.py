# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thames (UK) rand-generation profile — catchment-specific data only.

The shared property/commercial generators read these via
``port.rand.profiles.active_profile()``. Generation LOGIC is shared; only the
values that genuinely differ by catchment live here.
"""

# Seismic — UK intraplate: low PGA, None/Low-weighted hazard class.
SEISMIC_PGA_RANGE = (0.02, 0.08)
SEISMIC_HAZARD_CLASS_WEIGHTS = [0.70, 0.28, 0.02, 0.00, 0.00]

# BRI regime: Thames has no certified BRI letter-rating regime.
PUBLISH_BRI_LETTER_RATINGS = False
BRI_SCORES_ENABLED = False


# ---------------------------------------------------------------------------
# Commercial archetype tables (read by the shared commercial generators).
# Thames = UK market values; GBP service charges; no commercial BRI coding.
# ---------------------------------------------------------------------------

# Whether commercial assets carry the BRI Water/Flash/Wind/Fire/Seismic coding
# (thresholds, ratings, codes). Thames has no such regime -> fields blank/N-A.
COMMERCIAL_BRI_ENABLED = False

# First-slice fixed mix (Office x3, MultiFamily x3, Hotel, Retail x2, MixedUse);
# the type allocator cycles this beyond index 9.
COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]

# (min_sqm, max_sqm) — gross internal area
COMMERCIAL_TYPE_AREA_RANGE = {
    "Office":      (1500, 30000),
    "MultiFamily": (3000, 25000),
    "Hotel":       (4000, 35000),
    "Retail":      (500, 8000),
    "MixedUse":    (2500, 20000),
}

# GBP/sqm capital value
COMMERCIAL_TYPE_VALUE_PER_SQM = {
    "Office":      (8000, 15000),
    "MultiFamily": (5000, 10000),
    "Hotel":       (6000, 12000),
    "Retail":      (4000, 12000),
    "MixedUse":    (6000, 12000),
}

COMMERCIAL_TYPE_USE_CLASS = {
    "Office":      "E(g)(i)",
    "MultiFamily": "C3",
    "Hotel":       "C1",
    "Retail":      "E(a)",
    "MixedUse":    "E + C3",
}

COMMERCIAL_TYPE_BUSINESS_RATES = {
    "Office":      "Office",
    "MultiFamily": "Other",
    "Hotel":       "Hotel",
    "Retail":      "Shop and Premises",
    "MixedUse":    "Mixed",
}

COMMERCIAL_TYPE_STOREYS = {
    "Office":      (4, 25),
    "MultiFamily": (4, 20),
    "Hotel":       (4, 30),
    "Retail":      (1, 4),
    "MixedUse":    (3, 15),
}

COMMERCIAL_TYPE_TOTAL_UNITS = {
    "Office":      (1, 5),
    "MultiFamily": (30, 200),
    "Hotel":       (50, 350),
    "Retail":      (1, 12),
    "MixedUse":    (5, 100),
}

COMMERCIAL_TYPE_PARKING_SPACES = {
    "Office":      (20, 200),
    "MultiFamily": (10, 150),
    "Hotel":       (30, 200),
    "Retail":      (50, 400),
    "MixedUse":    (20, 150),
}

COMMERCIAL_TYPE_LOADING_BAYS = {
    "Office":      (0, 2),
    "MultiFamily": (0, 2),
    "Hotel":       (1, 4),
    "Retail":      (2, 8),
    "MixedUse":    (1, 4),
}

COMMERCIAL_CONSTRUCTION_TYPES = [
    "Steel frame", "Concrete frame", "Brick and block",
    "Modern methods", "Mixed construction",
]

COMMERCIAL_ANCHOR_TENANT_POOL = {
    "Office": ["Multi-let", "Multi-let", "Deloitte", "PwC", "Linklaters",
               "BlackRock", "Bloomberg", "Government Property Agency"],
    "MultiFamily": ["Multi-let"],
    "Hotel": ["IHG", "Marriott", "Accor", "Hilton", "Premier Inn",
              "Travelodge", "Mandarin Oriental"],
    "Retail": ["John Lewis", "Tesco", "Sainsbury's", "Boots",
               "Marks & Spencer", "Pret A Manger", "Multi-let"],
    "MixedUse": ["Multi-let"],
}

# (cutoff_year_exclusive, label); final entry has cutoff None (open-ended).
COMMERCIAL_PERIOD_BUCKETS = [
    (1919, "Pre-1919"),
    (1945, "1919-1944"),
    (1976, "1945-1975"),
    (2000, "1976-1999"),
    (2009, "2000-2008"),
    (None, "2009-Present"),
]
