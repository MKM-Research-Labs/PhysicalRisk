# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
