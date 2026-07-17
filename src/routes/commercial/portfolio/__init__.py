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
