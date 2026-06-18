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

"""Page 2: Location Details — thin wrapper around reports.asset.render_location.

Was a 200-line implementation; now delegates to the shared asset
section renderer so residential + commercial reports share the same
location rendering code.
"""

from typing import Any, Dict, List

from reports.asset import render_location

from .property_page_00_base import PropertyBasePage


class LocationPage(PropertyBasePage):
    """Renders the Location section from property_data['PropertyHeader']['Location']."""

    def generate_elements(
        self,
        property_data: Dict[str, Any],
        rloan_data: Dict[str, Any] = None,
    ) -> List:
        location = (property_data.get("PropertyHeader", {}) or {}).get("Location", {}) or {}
        return render_location(location, self)
