# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in port.rand.shared.
Phase 1 de-duplication: alias of the shared module (all symbols resolve)."""

import sys

from port.rand.shared.mortgage import quality as _canonical

sys.modules[__name__] = _canonical
