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
TYPE_AREA_RANGE = {
    "Office":      (1500, 30000),
    "MultiFamily": (3000, 25000),
    "Hotel":       (4000, 35000),
    "Retail":      (500, 8000),
    "MixedUse":    (2500, 20000),
}

# £/sqm capital value
TYPE_VALUE_PER_SQM = {
    "Office":      (8000, 15000),
    "MultiFamily": (5000, 10000),
    "Hotel":       (6000, 12000),
    "Retail":      (4000, 12000),
    "MixedUse":    (6000, 12000),
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

# (min_storeys, max_storeys)
TYPE_STOREYS = {
    "Office":      (4, 25),
    "MultiFamily": (4, 20),
    "Hotel":       (4, 30),
    "Retail":      (1, 4),
    "MixedUse":    (3, 15),
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
