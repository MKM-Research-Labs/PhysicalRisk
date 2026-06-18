# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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
