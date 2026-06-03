# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Commercial-asset routes package.

Splits the former single ``routes/commercial.py`` module into focused
sub-modules that all register on one shared blueprint:

- reports:   PDF report + loan-report endpoints
- pricing:   loan-pricer endpoint
- storms:    storm-scenario endpoint + catchment enrichment helpers
- hazard:    hazard-curve (hc/she/shd/bri) + asset-record endpoints
- portfolio: list / blotter / per-storm portfolio-impact endpoints

``commercial_bp`` is re-exported so ``routes.registry`` can keep doing
``from .commercial import commercial_bp`` unchanged.
"""

from .blueprint import commercial_bp  # noqa: F401

# Import sub-modules to register their routes on commercial_bp.
from . import reports    # noqa: E402, F401
from . import pricing    # noqa: E402, F401
from . import storms     # noqa: E402, F401
from . import hazard     # noqa: E402, F401
from . import portfolio  # noqa: E402, F401
