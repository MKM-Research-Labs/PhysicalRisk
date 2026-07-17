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

"""
FS01 circles on the main Leaflet map.

Duplicates the Aggregate tab's circle display on the main map,
showing net FS01 exposure per gauge with scaled, color-coded circles.
Auto-refreshes after trade commits or close-outs.
"""

import folium

from visual.interactivity._jsbundle import js_static


class MainMapFS01:
    """Adds FS01 exposure circles to the main map."""

    def get_js(self) -> str:
        """Generate JavaScript for main map FS01 circles.

        The panel JavaScript lives in ``src/static/js/td-main-map.js``.
        """
        return f"<script>\n{js_static('td-main-map.js')}</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add FS01 circles to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))

    def get_statistics(self):
        return {"component": "main_map_fs01"}
