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
Map controls configuration and application.
"""

import logging

import folium
from folium import plugins

logger = logging.getLogger(__name__)


class MapControls:
    """Configuration and application of Folium map controls."""

    def __init__(self, measure: bool = True, fullscreen: bool = True,
                 layer_control: bool = True, scale: bool = True):
        """
        Initialize control settings.

        Args:
            measure: Add measurement tool
            fullscreen: Add fullscreen button
            layer_control: Add layer toggle control
            scale: Add scale indicator
        """
        self.measure = measure
        self.fullscreen = fullscreen
        self.layer_control = layer_control
        self.scale = scale

    def apply_to_map(self, folium_map: folium.Map, include_layer_control: bool = False):
        """
        Apply configured controls to a map.

        Args:
            folium_map: Map to add controls to
            include_layer_control: Whether to add layer control now (often added at finalize)
        """
        try:
            if self.measure:
                plugins.MeasureControl(
                    position='bottomleft',
                    primary_length_unit='kilometers',
                    secondary_length_unit='miles'
                ).add_to(folium_map)

            if self.fullscreen:
                plugins.Fullscreen(position='topleft').add_to(folium_map)

            if include_layer_control and self.layer_control:
                folium.LayerControl().add_to(folium_map)

        except Exception as e:
            logger.warning("Could not add some map controls: %s", e)

    def add_layer_control(self, folium_map: folium.Map):
        """Add layer control to the map (typically called at finalize)."""
        if self.layer_control:
            try:
                folium.LayerControl().add_to(folium_map)
            except Exception as e:
                logger.warning("Could not add layer control: %s", e)
