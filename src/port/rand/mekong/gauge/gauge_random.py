# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in
``port.rand.shared.gauge.gauge_random``.

Phase 1 de-duplication: thames and halong share ONE implementation. This module
is an alias of the shared canonical module, so every symbol (public and
private) resolves through it. Do not add catchment-specific logic here;
per-catchment data belongs in the catchment profile, not a forked copy.
"""

import sys

from port.rand.shared.gauge import gauge_random as _canonical

sys.modules[__name__] = _canonical
