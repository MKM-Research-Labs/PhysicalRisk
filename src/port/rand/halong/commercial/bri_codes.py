# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Catchment shim — canonical implementation in
``port.rand.shared.commercial.bri_codes``.

Alias of the shared module so every symbol (public and private) resolves
through it. The BRI commercial catalogue is regional data consumed only when
the active profile sets ``COMMERCIAL_BRI_ENABLED``; do not fork it here.
"""

import sys

from port.rand.shared.commercial import bri_codes as _canonical

sys.modules[__name__] = _canonical
