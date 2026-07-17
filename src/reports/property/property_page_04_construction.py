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

"""Page 4: Construction Details — thin wrapper around render_construction.

Was a ~200-line implementation; now delegates to the shared asset
section renderer.
"""

from typing import Any, Dict, List

from reports.asset import render_construction

from .property_page_00_base import PropertyBasePage


class ConstructionPage(PropertyBasePage):
    """Renders Construction from property_data['PropertyHeader']['Construction']."""

    def generate_elements(
        self,
        property_data: Dict[str, Any],
        rloan_data: Dict[str, Any] = None,
    ) -> List:
        section = (property_data.get("PropertyHeader", {}) or {}).get("Construction", {}) or {}
        return self._emit_or_fallback(
            section, "Construction Details", render_construction,
            "No construction data available.",
        )
