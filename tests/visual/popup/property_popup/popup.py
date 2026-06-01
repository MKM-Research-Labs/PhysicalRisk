# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for create_complete_popup_content and build_property_popup."""

import pytest
import folium


# ---------------------------------------------------------------------------
# create_complete_popup_content
# ---------------------------------------------------------------------------

class TestCreateCompletePopupContent:

    def _build(self, builder, prop, address, flood_info=None,
               has_rloan=False, rloan_info=None):
        return builder.create_complete_popup_content(
            prop=prop,
            property_id='PROP-aabbccdd',
            address=address,
            coordinates='51.5°N, -0.1°E',
            flood_risk='Medium',
            thames_proximity='Close',
            ground_elevation=8.5,
            elevation_estimated=False,
            property_value=450000,
            construction_year=1988,
            property_age_factor='Older (pre-1990)',
            has_rloan=has_rloan,
            rloan_info=rloan_info,
            flood_info=flood_info,
        )

    def test_contains_header_with_id(self, builder, prop, address):
        html = self._build(builder, prop, address)
        assert 'PROP-aabbccdd' in html

    def test_contains_header_title(self, builder, prop, address):
        html = self._build(builder, prop, address)
        assert 'Property Analysis' in html

    def test_contains_property_section(self, builder, prop, address):
        html = self._build(builder, prop, address)
        assert 'Property Information' in html

    def test_no_flood_section_when_none(self, builder, prop, address):
        html = self._build(builder, prop, address, flood_info=None)
        assert 'Flood Risk Information' not in html

    def test_flood_section_present_when_supplied(self, builder, prop, address, flood_info):
        html = self._build(builder, prop, address, flood_info=flood_info)
        assert 'Chelsea Gauge' in html

    def test_no_rloan_section_when_has_mortgage_false(self, builder, prop, address, rloan_info):
        html = self._build(builder, prop, address, has_rloan=False, rloan_info=rloan_info)
        assert 'MORTGAGE DETAILS' not in html

    def test_no_rloan_section_when_mortgage_info_none(self, builder, prop, address):
        html = self._build(builder, prop, address, has_rloan=True, rloan_info=None)
        assert 'MORTGAGE DETAILS' not in html

    def test_rloan_section_present_when_has_mortgage(self, builder, prop, address,
                                                         flood_info, rloan_info):
        html = self._build(builder, prop, address, flood_info=flood_info,
                           has_rloan=True, rloan_info=rloan_info)
        assert 'MORTGAGE DETAILS' in html

    def test_wrapped_in_popup_div(self, builder, prop, address):
        html = self._build(builder, prop, address)
        assert '<div' in html
        assert 'font-family' in html

    def test_returns_string(self, builder, prop, address):
        html = self._build(builder, prop, address)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_all_sections_combined(self, builder, prop, address, flood_info,
                                   rloan_info):
        html = self._build(builder, prop, address, flood_info=flood_info,
                           has_rloan=True, rloan_info=rloan_info)
        assert 'Property Information' in html
        assert 'Chelsea Gauge' in html
        assert 'MORTGAGE DETAILS' in html


# ---------------------------------------------------------------------------
# build_property_popup
# ---------------------------------------------------------------------------

class TestBuildPropertyPopup:

    def _popup(self, builder, prop, address, **kwargs):
        defaults = dict(
            flood_risk='Low',
            thames_proximity='Distant',
            ground_elevation=12.0,
            elevation_estimated=False,
            property_value=350000,
            construction_year=2000,
            property_age_factor='New (post-1991)',
            has_rloan=False,
        )
        defaults.update(kwargs)
        return builder.build_property_popup(
            prop=prop,
            property_id='PROP-aabbccdd',
            address=address,
            coordinates='51.5°N, -0.1°E',
            **defaults,
        )

    def test_returns_folium_popup(self, builder, prop, address):
        popup = self._popup(builder, prop, address)
        assert isinstance(popup, folium.Popup)

    def test_popup_is_not_none(self, builder, prop, address):
        assert self._popup(builder, prop, address) is not None

    def test_popup_with_no_optional_params(self, builder, prop, address):
        popup = self._popup(builder, prop, address)
        assert popup is not None

    def test_popup_with_all_optional_params(self, builder, prop, address,
                                            flood_info, rloan_info):
        popup = self._popup(
            builder, prop, address,
            flood_risk='High',
            has_rloan=True,
            flood_info=flood_info,
            rloan_info=rloan_info,
        )
        assert isinstance(popup, folium.Popup)

    def test_popup_attachable_to_marker(self, builder, prop, address):
        popup = self._popup(builder, prop, address)
        m = folium.Map(location=[51.5, -0.1])
        folium.Marker(location=[51.5, -0.1], popup=popup).add_to(m)
        assert len(m._repr_html_()) > 0

    def test_popup_html_contains_property_id(self, builder, prop, address):
        popup = self._popup(builder, prop, address)
        assert 'PROP-aabbccdd' in popup.html.render()

    def test_popup_html_contains_address(self, builder, prop, address):
        popup = self._popup(builder, prop, address)
        assert 'Flood Lane' in popup.html.render()

