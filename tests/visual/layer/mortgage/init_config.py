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

"""
Tests for MortgageLayer.__init__ and configure.
"""

import pytest
import folium

from visual.layer.mortgage_layer.layer import MortgageLayer


class TestMortgageLayerInit:

    def test_layer_name(self):
        assert MortgageLayer().layer_name == "Mortgage Risk"

    def test_show_risk_circles_default(self):
        assert MortgageLayer().show_risk_circles is True

    def test_show_ltv_indicators_default(self):
        assert MortgageLayer().show_ltv_indicators is True

    def test_circle_opacity_default(self):
        assert MortgageLayer().circle_opacity == pytest.approx(0.4)

    def test_max_circle_radius_default(self):
        assert MortgageLayer().max_circle_radius == 500


class TestMortgageConfigure:

    def test_configure_all_params(self):
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False, show_ltv_indicators=False,
                        circle_opacity=0.7, max_circle_radius=800)
        assert layer.show_risk_circles is False
        assert layer.show_ltv_indicators is False
        assert layer.circle_opacity == pytest.approx(0.7)
        assert layer.max_circle_radius == 800

    def test_configure_defaults(self):
        layer = MortgageLayer()
        layer.configure()
        assert layer.show_risk_circles is True
        assert layer.show_ltv_indicators is True
        assert layer.circle_opacity == pytest.approx(0.4)
        assert layer.max_circle_radius == 500

    def test_configure_partial(self):
        layer = MortgageLayer()
        layer.configure(show_risk_circles=False)
        assert layer.show_risk_circles is False
        assert layer.show_ltv_indicators is True
