# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.
"""Commercial list / blotter / per-storm portfolio-impact endpoints.

  GET /api/v1/commercial            (list all commercial assets)
  GET /api/v1/commercial-loans      (list all commercial loans)
      Used by the startup preloader for the bottom-left status popup
      and the in-browser asset-name lookup.

  GET /api/v1/commercial/blotter
      Commercial-asset portfolio blotter. Mirrors
      /api/v1/propertyts/blotter — used by the Storm Portfolio Table tab.

  GET /api/v1/commercial/<storm_id>/portfolio-impact
      Per-storm commercial damage. Mirrors
      /api/v1/propertyts/<storm_id>/portfolio-impact.
"""

from . import _blotter, _impact, _list  # noqa: E402, F401  (register routes)
