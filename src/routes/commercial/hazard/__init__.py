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
