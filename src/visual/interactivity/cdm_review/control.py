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

"""CdmReviewControl — adds the CDM Asset Review house icon to the map.

Icon-only control (no in-app panel): clicking it opens the CDM Asset Review
workstream at ``/cdm-asset-review``. The JavaScript lives in the companion
``src/static/js/cdm_review/control.js`` (loaded verbatim); this module only
wraps it in a <script> tag and attaches it to the Folium map.
"""

import folium

from visual.interactivity._jsbundle import js_static


class CdmReviewControl:
    """Handler for the CDM Asset Review map launcher icon."""

    def get_js(self) -> str:
        return f"<script>\n{js_static('cdm_review/control.js')}\n</script>"

    def add_to_map(self, folium_map: folium.Map) -> None:
        """Add the CDM Asset Review control to a Folium map."""
        folium_map.get_root().html.add_child(folium.Element(self.get_js()))
