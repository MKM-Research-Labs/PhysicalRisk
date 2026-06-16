# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in
``port.rand.shared.property.property_random.generators`` (Phase 2). Catchment-
specific values (seismic ranges, …) come from port.rand.profiles.<catchment>."""

import sys

from port.rand.shared.property.property_random import generators as _canonical

sys.modules[__name__] = _canonical
