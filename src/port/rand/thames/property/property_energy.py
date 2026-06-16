# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in
``port.rand.shared.property.property_energy``.

Phase 1 de-duplication: thames and halong share one implementation. Do not add
catchment-specific logic here; per-catchment data belongs in the catchment
profile, not a forked copy.
"""

from port.rand.shared.property.property_energy import *  # noqa: F401,F403
