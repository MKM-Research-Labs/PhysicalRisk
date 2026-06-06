# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)
"""
Asset header schema — identifiers, valuation, attributes, construction, location.

Carries the full PropertyHeader schema as it existed in the legacy
property/schema/header.py. The residential/commercial split (e.g.
moving NumberBedrooms/CouncilTaxBand into asset/residential/header.py)
will happen on a later pass — this file is currently asset-wide so
the legacy property pipeline keeps emitting byte-identical JSON.
"""

from ._attributes import PROPERTY_ATTRIBUTES
from ._construction import CONSTRUCTION
from ._identity import HEADER, VALUATION
from ._location import LOCATION

HEADER_SCHEMA = {
    "Header": HEADER,
    "Valuation": VALUATION,
    "PropertyAttributes": PROPERTY_ATTRIBUTES,
    "Construction": CONSTRUCTION,
    "Location": LOCATION,
}
