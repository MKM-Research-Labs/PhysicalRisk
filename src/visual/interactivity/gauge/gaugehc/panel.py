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
GaugeHazardCurve panel — assembles the full 6-tab gauge hazard panel.

Composes sub-module JavaScript (ghc_hazard, ghc_return, ghc_prs,
ghc_historical, ghc_stress) into a single IIFE and attaches it to
the Folium map.
"""

from typing import Any, Dict

import folium

from . import ghc_hazard, ghc_return, ghc_prs, ghc_historical, ghc_stress
from .panel_create import get_create_panel_js
from .panel_nav import get_nav_js
from visual.interactivity.panel_mixin import FoliumPanelMixin
from .panel_data import get_data_js


class GaugeHazardCurve(FoliumPanelMixin):
    """Handler for interactive gauge hazard curve dashboard."""

    def __init__(self,
                 panel_width: str = "1100px",
                 panel_height: str = "750px"):
        self.panel_width = panel_width
        self.panel_height = panel_height

    def get_js(self) -> str:
        """Generate JavaScript for gauge hazard curve panel."""
        return f"""
        <script>
        (function() {{
            var PANEL_W = '{self.panel_width}';
            var PANEL_H = '{self.panel_height}';
            var currentChart = null;
            var hazardPanel = null;
            var hazardData = null;
            var counterpartyData = [];

            // ==============================================================
            // Sub-module code (state vars + functions)
            // ==============================================================
{ghc_hazard.get_js()}
{ghc_return.get_js()}
{ghc_prs.get_js()}
{ghc_historical.get_js()}
{ghc_stress.get_js()}

{get_create_panel_js()}
{get_nav_js()}
{get_data_js()}

            // ================================================================
            // Event listeners
            // ================================================================
            document.addEventListener('hazardCurveRequested', function(e) {{
                if (e.detail && e.detail.gaugeId) showPanel(e.detail.gaugeId);
            }});

            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape' && hazardPanel && hazardPanel.style.display !== 'none') {{
                    hidePanel();
                }}
            }});

            window.GaugeHazardCurve = {{
                show: showPanel,
                hide: hidePanel
            }};

            console.log('Gauge hazard curve ready');
        }})();
        </script>
        """

    # add_to_map, configure, get_statistics inherited from FoliumPanelMixin
