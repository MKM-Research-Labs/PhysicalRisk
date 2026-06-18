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

"""
Global page-load startup preloader.

Runs on DOMContentLoaded and pre-fetches ALL data needed across every panel:
storms, trader data, governance documents, gauge locations.  Shows a centered
progress popup with a spinner-to-tick row per dataset.

Panels consume the pre-fetched data via window._pre* cache variables so that
opening any panel for the first time is instant (no waiting for a fetch).

The popup DOM creation and per-item status helpers live in the sibling
``startup_popup`` module and are concatenated into the same IIFE.

Datasets pre-fetched:
  _tdPreBlotter      — /api/v1/trading/blotter
  _tdPreMarket       — /api/v1/trading/market-state       (label: Hazard curves)
  _tdPreGauges       — /api/v1/gauges
  _tdPreStressStorms — /api/v1/trading/stress/storms
  _tdPrePortStorms   — /api/v1/trading/stress/portfolio-storms
  _tdPreEodHistory   — /api/v1/trading/eod/history
  _tdPreYieldCurve   — /api/v1/trading/yield-curve
  _tdPreGovDocs      — /api/v1/governance/documents
  _preStorms         — /api/v1/propertyts/storms
  _preGovAudit       — /api/v1/governance/audit-trail?limit=200
  _preGovBib         — /api/v1/governance/bibliography
  _prePropertyTS     — /api/v1/propertyts/summary
  _preGaugeHist      — /api/v1/gauges/history/summary
  _preCommercial     — /api/v1/commercial            (Commercial assets count)
  _preCommercialLoans — /api/v1/commercial-loans     (Commercial loans count)
"""

from visual.interactivity._jsbundle import js_static

from . import startup_popup as _startup_popup


class StartupPreloader:
    """Adds the global page-load preloader to a Folium map."""

    def add_to_map(self, folium_map) -> None:
        import folium as _folium
        folium_map.get_root().html.add_child(_folium.Element(
            f"<script>\n(function(){{\n{_get_preloader_js()}\n}})();\n</script>"
        ))


def _get_preloader_js() -> str:
    """Return the JS body for the global startup preloader (no wrapping IIFE)."""
    return get_js()


def get_js() -> str:
    """Return JS fragment for the global startup preloader."""
    cache_init_and_main = js_static('startup.js')
    return cache_init_and_main + _startup_popup.get_js()
