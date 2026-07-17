# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
