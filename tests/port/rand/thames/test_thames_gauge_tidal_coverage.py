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

"""Coverage tests for the thames gauge TidalInfluence fallbacks — mirrors the
halong tidal tests: missing longitude and a bounds-lookup failure both yield
"Non-tidal"."""

from port.rand.thames.gauge import gauge_field_generators as gfg


class TestThamesTidalFallbacks:
    def test_missing_lon_returns_non_tidal(self):
        meta = {"location": {"lon": None}}
        assert gfg.generate_menu_value("TidalInfluence", {}, 0, meta) == "Non-tidal"  # 256

    def test_bounds_error_returns_non_tidal(self, monkeypatch):
        def _boom():
            raise RuntimeError("no catchment bounds")

        monkeypatch.setattr(gfg, "get_catchment_bounds", _boom)
        meta = {"location": {"lon": -0.1}}
        assert gfg.generate_menu_value("TidalInfluence", {}, 0, meta) == "Non-tidal"  # 261-262
