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
