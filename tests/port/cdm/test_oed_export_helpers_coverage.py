# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
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
