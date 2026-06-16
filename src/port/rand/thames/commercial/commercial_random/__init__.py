# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in
``port.rand.shared.commercial.commercial_random``.

Alias of the shared module so every symbol (public and private) resolves
through it. Per-catchment commercial data lives in the catchment profile,
not a forked copy here.
"""

import sys

from port.rand.shared.commercial import commercial_random as _canonical

sys.modules[__name__] = _canonical
