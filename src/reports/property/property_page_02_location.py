# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
