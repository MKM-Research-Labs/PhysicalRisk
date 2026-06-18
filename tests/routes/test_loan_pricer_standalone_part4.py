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

"""Standalone loan-pricer tests (part 4) — independent peril toggles.

The calculator's storm/flood MENU sets the flood/wind basis; fire and seismic
are binary on/off BUTTONS (include_fire / include_seismic). Each toggled-on leg
is folded into the all-in coupon by root-sum-of-squares, matching the PRS
pricer. With both toggles off the coupon is unchanged.
"""

import math

import pytest


class TestIndependentPerilToggles:

    def _coupon(self, client, **inputs):
        base = {"loan_amount": 200000, "property_value": 300000}
        r = client.post("/api/v1/loan-pricer", json={"inputs": {**base, **inputs}})
        assert r.status_code == 200
        return r.get_json()["coupon"]

    def test_toggles_off_leave_basis_unchanged(self, prop_client):
        client, _ = prop_client
        # Spreads present but both toggles off -> all-in == basis.
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=400,
                         fire_spread_bps=300, seismic_spread_bps=200,
                         include_fire=False, include_seismic=False)
        assert c["hazard_spread"] == pytest.approx(0.040)
        assert c["flood_wind_base"] == pytest.approx(0.040)
        assert c["fire_included"] is False
        assert c["seismic_included"] is False

    def test_fire_toggle_rss(self, prop_client):
        client, _ = prop_client
        # 400 basis + 300 fire -> sqrt(400^2 + 300^2) = 500 bps (3-4-5).
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=400,
                         fire_spread_bps=300, include_fire=True)
        assert c["fire_included"] is True
        assert c["fire_spread"] == pytest.approx(0.030)
        assert c["flood_wind_base"] == pytest.approx(0.040)
        assert c["hazard_spread"] == pytest.approx(0.050)

    def test_seismic_toggle_rss(self, prop_client):
        client, _ = prop_client
        # 300 basis + 400 seismic -> sqrt(300^2 + 400^2) = 500 bps.
        c = self._coupon(client, prs_scenario="flo", prs_spread_bps=300,
                         seismic_spread_bps=400, include_seismic=True)
        assert c["seismic_included"] is True
        assert c["seismic_spread"] == pytest.approx(0.040)
        assert c["hazard_spread"] == pytest.approx(0.050)

    def test_both_toggles_rss(self, prop_client):
        client, _ = prop_client
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=120,
                         fire_spread_bps=160, seismic_spread_bps=90,
                         include_fire=True, include_seismic=True)
        expected = math.sqrt(120**2 + 160**2 + 90**2) / 10000.0
        assert c["hazard_spread"] == pytest.approx(expected)
        assert c["fire_included"] and c["seismic_included"]

    def test_toggle_on_without_asset_leg_is_noop(self, prop_client):
        client, _ = prop_client
        # Toggle on but no fire leg supplied -> shown as included, leg 0, basis
        # unchanged (sqrt(basis^2 + 0) == basis).
        c = self._coupon(client, prs_scenario="fow", prs_spread_bps=400,
                         include_fire=True)
        assert c["fire_included"] is True
        assert c["fire_spread"] == pytest.approx(0.0)
        assert c["hazard_spread"] == pytest.approx(0.040)

    def test_default_path_rss_with_seismic(self, prop_client):
        client, _ = prop_client
        # No PRS scenario -> flood+wind basis; seismic folds in by RSS.
        c = self._coupon(client, seismic_spread_bps=300, include_seismic=True)
        base = c["flood_wind_base"]
        expected = math.sqrt(base ** 2 + 0.030 ** 2)
        assert c["hazard_spread"] == pytest.approx(expected)
        assert c["seismic_included"] is True
