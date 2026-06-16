# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Catchment resilience facade.

All logic lives in ``port.rand.shared.property_resilience``; the two per-catchment
BRI toggles come from this catchment's profile. The shared installer populates
this module (re-exports + toggles + wrappers) from the catchment id in
``__name__`` — so this file is identical for every catchment.
"""

from port.rand.shared.property.property_random._resilience_facade import install

install(__name__)
