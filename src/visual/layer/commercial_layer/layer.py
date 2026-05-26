# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""CommercialLayer — adds commercial-asset markers to the Folium map."""

import logging
from typing import Any, Dict, List, Optional

import folium

from .popup import create_commercial_popup
from .stats import get_commercial_statistics

logger = logging.getLogger(__name__)


# Distinct Font-Awesome icons per CommercialType. Anything not in the
# table falls back to 'industry'.
_ICON_BY_TYPE = {
    "Office":      "briefcase",
    "MultiFamily": "building",
    "Hotel":       "hotel",
    "Retail":      "shopping-cart",
    "Leisure":     "glass-cheers",
    "Healthcare":  "hospital",
    "MixedUse":    "city",
}

# All commercial markers share a purple palette so they're visually
# distinct from residential (green/orange/red) and gauges (blue).
_MARKER_COLOR = "purple"
_LAYER_NAME = "Commercial Assets"


class CommercialLayer:
    """Layer class for adding commercial-asset markers to the map."""

    def __init__(self):
        self.layer_name = _LAYER_NAME

    def add_to_map(self, folium_map: folium.Map, loaded_data) -> folium.FeatureGroup:
        """Add the commercial layer to the map. No-ops when there are no
        commercial assets loaded."""
        logger.info(f"Adding {self.layer_name} to map...")

        group = folium.FeatureGroup(name=self.layer_name)
        assets = self._extract_assets(loaded_data)
        if not assets:
            logger.info("No commercial assets to render")
            return group

        loan_lookup = getattr(loaded_data, "commercial_loan_lookup", None) or {}

        count = 0
        for asset in assets:
            try:
                if self._add_marker(group, asset, loan_lookup):
                    count += 1
            except Exception as e:
                logger.warning(f"Error rendering commercial asset: {e}")

        group.add_to(folium_map)
        logger.info(f"Added {count} commercial assets to map")
        return group

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_assets(loaded_data) -> List[Dict[str, Any]]:
        data = getattr(loaded_data, "commercial_data", None) or {}
        return data.get("commercial_assets", [])

    @staticmethod
    def _add_marker(group: folium.FeatureGroup, asset: Dict[str, Any],
                    loan_lookup: Dict[str, Dict]) -> bool:
        ca = asset.get("CommercialAsset", {})
        location = ca.get("Location", {})
        attrs = ca.get("CommercialAttributes", {})
        header = ca.get("Header", {})

        lat = location.get("LatitudeDegrees")
        lon = location.get("LongitudeDegrees")
        if lat is None or lon is None:
            return False

        pid = header.get("PropertyID", "")
        ctype = attrs.get("CommercialType", "Other")
        icon_name = _ICON_BY_TYPE.get(ctype, "industry")
        loan = loan_lookup.get(pid)

        popup_html = create_commercial_popup(asset, loan)
        has_loan = " | Loan" if loan else ""
        tooltip = f"{ctype} — {pid}{has_loan}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=tooltip,
            icon=folium.Icon(color=_MARKER_COLOR, icon=icon_name, prefix="fa"),
        ).add_to(group)
        return True

    # Convenience for tests / report generators
    def get_commercial_statistics(self, loaded_data) -> Dict[str, Any]:
        return get_commercial_statistics(self._extract_assets(loaded_data))
