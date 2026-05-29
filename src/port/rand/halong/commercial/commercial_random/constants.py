# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Per-CommercialType parameter tables for the commercial generators.

The 10-asset first-slice allocation lives here too — the user-requested
mix is fixed (Office x3, MultiFamily x3, Hotel, Retail x2, MixedUse).
Beyond index 9 the type allocator cycles.
"""

COMMERCIAL_TYPE_ALLOCATION = [
    "Office", "Office", "Office",
    "MultiFamily", "MultiFamily", "MultiFamily",
    "Hotel",
    "Retail", "Retail",
    "MixedUse",
]


# (min_sqm, max_sqm) — gross internal area
# Halong ranges are centred on the BRI-PRS SE-Asia building prototypes
# (data/catch/halong/BRI-PRS Building Prototypes.xlsx). Midpoints align
# with the prototypes: MixedUse 40k, MultiFamily 30k, Hotel 45k.
TYPE_AREA_RANGE = {
    "Office":      (10000, 40000),     # mean 25k (no prototype anchor)
    "MultiFamily": (20000, 40000),     # mean 30k → Bldg 2
    "Hotel":       (35000, 55000),     # mean 45k → Bldg 3
    "Retail":      (500, 8000),        # unchanged — small-footprint stock
    "MixedUse":    (30000, 50000),     # mean 40k → Bldg 1
}

# USD/sqm capital value. SE-Asia pricing — much lower than UK commercial.
# Means picked so (mean sqm × mean value/sqm) ≈ prototype total value:
#   MixedUse  40k × 625 = $25M  → Bldg 1
#   MultiFamily 30k × 675 = $20.25M → Bldg 2
#   Hotel     45k × 675 = $30M  → Bldg 3
TYPE_VALUE_PER_SQM = {
    "Office":      (500, 800),
    "MultiFamily": (550, 800),
    "Hotel":       (550, 800),
    "Retail":      (800, 1500),
    "MixedUse":    (500, 750),
}

TYPE_USE_CLASS = {
    "Office":      "E(g)(i)",
    "MultiFamily": "C3",
    "Hotel":       "C1",
    "Retail":      "E(a)",
    "MixedUse":    "E + C3",
}

TYPE_BUSINESS_RATES = {
    "Office":      "Office",
    "MultiFamily": "Other",
    "Hotel":       "Hotel",
    "Retail":      "Shop and Premises",
    "MixedUse":    "Mixed",
}

# (min_storeys, max_storeys). Halong ranges centred on the BRI-PRS
# prototypes: MixedUse 15, MultiFamily 25, Hotel 20.
TYPE_STOREYS = {
    "Office":      (8, 22),            # mean ~15
    "MultiFamily": (20, 30),           # mean 25 → Bldg 2
    "Hotel":       (15, 25),           # mean 20 → Bldg 3
    "Retail":      (1, 4),             # unchanged
    "MixedUse":    (10, 20),           # mean 15 → Bldg 1
}

TYPE_TOTAL_UNITS = {
    "Office":      (1, 5),
    "MultiFamily": (30, 200),
    "Hotel":       (50, 350),
    "Retail":      (1, 12),
    "MixedUse":    (5, 100),
}

TYPE_PARKING_SPACES = {
    "Office":      (20, 200),
    "MultiFamily": (10, 150),
    "Hotel":       (30, 200),
    "Retail":      (50, 400),
    "MixedUse":    (20, 150),
}

TYPE_LOADING_BAYS = {
    "Office":      (0, 2),
    "MultiFamily": (0, 2),
    "Hotel":       (1, 4),
    "Retail":      (2, 8),
    "MixedUse":    (1, 4),
}

# Construction options applicable to commercial buildings (steel/concrete
# frame dominate; the residential menu includes them).
COMMERCIAL_CONSTRUCTION_TYPES = [
    "Steel frame", "Concrete frame", "Brick and block",
    "Modern methods", "Mixed construction",
]


ANCHOR_TENANT_POOL = {
    "Office": ["Multi-let", "Multi-let", "Deloitte", "PwC", "Linklaters",
               "BlackRock", "Bloomberg", "Government Property Agency"],
    "MultiFamily": ["Multi-let"],
    "Hotel": ["IHG", "Marriott", "Accor", "Hilton", "Premier Inn",
              "Travelodge", "Mandarin Oriental"],
    "Retail": ["John Lewis", "Tesco", "Sainsbury's", "Boots",
               "Marks & Spencer", "Pret A Manger", "Multi-let"],
    "MixedUse": ["Multi-let"],
}
