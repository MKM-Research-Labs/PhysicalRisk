# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
