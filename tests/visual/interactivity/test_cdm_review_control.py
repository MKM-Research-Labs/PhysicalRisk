# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Tests for visual.interactivity.cdm_review — the CDM Asset Review map icon.

Covers: the control JS carries the house icon and routes to /cdm-asset-review,
opens an in-app panel (not a new tab), and injects into a Folium map.
"""

import folium

from visual.interactivity.cdm_review import CdmReviewControl


class TestCdmReviewControl:

    def test_get_js_is_script_wrapped(self):
        js = CdmReviewControl().get_js()
        assert js.strip().startswith("<script>")
        assert js.strip().endswith("</script>")

    def test_has_house_icon_and_route(self):
        js = CdmReviewControl().get_js()
        assert "CdmReviewControl" in js
        assert "/cdm-asset-review" in js
        assert "<svg" in js  # house icon

    def test_opens_in_app_panel_not_new_tab(self):
        js = CdmReviewControl().get_js()
        # Stays on the tab like the other workstreams — no new window.
        assert "window.open" not in js
        assert "cdm-review-panel" in js
        assert "iframe" in js

    def test_stacks_at_topright(self):
        js = CdmReviewControl().get_js()
        assert "topright" in js

    def test_add_to_map_injects_control(self):
        m = folium.Map(location=[51.5, -0.1], zoom_start=10)
        CdmReviewControl().add_to_map(m)
        html = m.get_root().render()
        assert "cdm-review-panel" in html
        assert "/cdm-asset-review" in html
