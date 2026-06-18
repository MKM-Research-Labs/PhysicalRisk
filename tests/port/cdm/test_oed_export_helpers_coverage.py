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

"""Coverage tests for oed_export._helpers — the _currency config fallback
and the _lookup_str None-key / mapping branches."""

from port.cdm.oed_export import _helpers


class TestOedHelpersCoverage:
    def test_currency_falls_back_to_gbp_on_error(self, monkeypatch):
        import config as config_pkg

        class _Boom:
            @property
            def CURRENCY(self):
                raise RuntimeError("config unavailable")

        monkeypatch.setattr(config_pkg, "config", _Boom())
        assert _helpers._currency() == "GBP"  # lines 40-41

    def test_currency_returns_config_value(self, monkeypatch):
        import config as config_pkg

        class _Cfg:
            CURRENCY = "EUR"

        monkeypatch.setattr(config_pkg, "config", _Cfg())
        assert _helpers._currency() == "EUR"

    def test_lookup_str_none_key_returns_default(self):
        assert _helpers._lookup_str({"a": "x"}, None, default="D") == "D"  # 51-52

    def test_lookup_str_returns_mapped_or_default(self):
        assert _helpers._lookup_str({"a": "x"}, "a") == "x"            # line 53
        assert _helpers._lookup_str({"a": "x"}, "miss", default="d") == "d"  # line 53
