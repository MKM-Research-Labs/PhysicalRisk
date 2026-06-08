# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial hazard-curve / PRS-pricing endpoints package.

  GET /api/v1/commercial/<prop_id>/hazard
  GET /api/v1/commercial/<prop_id>/she
  GET /api/v1/commercial/<prop_id>/shd
  GET /api/v1/commercial/<prop_id>/bri
  GET /api/v1/commercial/<prop_id>/win   (wind-only peril)
  GET /api/v1/commercial/<prop_id>/faw   (flood AND wind)
  GET /api/v1/commercial/<prop_id>/fow   (flood OR wind)
  GET /api/v1/commercial/<prop_id>/bow   (BRI OR wind)
  GET /api/v1/commercial/<prop_id>/baw   (BRI AND wind)
  GET /api/v1/commercial/<prop_id>       (bare asset record for address lookup)

This ``__init__`` only assembles the package: the route handlers live in
``_routes.py`` and their functional helpers (loaders + fire/seismic read-time
joins) in ``_helpers.py``. Importing ``_routes`` registers the handlers on
``commercial_bp``.
"""

# Side-effect import: registers the route handlers on commercial_bp.
from . import _routes  # noqa: F401
