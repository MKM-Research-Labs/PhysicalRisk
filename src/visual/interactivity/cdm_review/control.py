# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

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
