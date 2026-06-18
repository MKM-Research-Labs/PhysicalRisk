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
