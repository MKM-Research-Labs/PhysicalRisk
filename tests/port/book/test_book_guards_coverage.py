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

"""Coverage tests for port.src.book.book — the no-real-curves guard and the
print_book_summary currency fallback. (The REIT-skip line needs full book
generation and is left for a later tranche.)"""

import pytest
from db_helpers import tmp_catchment

import database
from port.src.book import book

_CATCHMENT = "thames"


class TestBookGuards:
    def test_raises_when_only_synthetic_curves(self, tmp_path):
        with tmp_catchment(tmp_path, _CATCHMENT):
            database.save_gauge_hazard_curves(
                _CATCHMENT, {"hazard_curves": {"SYNTH-1": {}, "SYNTH-2": {}}})
            with pytest.raises(ValueError, match="non-SYNTH"):
                book.generate_market_making_book(output_dir=tmp_path)

    def test_print_book_summary_currency_falls_back_to_gbp(self, monkeypatch):
        import config as config_pkg

        class _Boom:
            @property
            def CURRENCY(self):
                raise RuntimeError("no config")

        monkeypatch.setattr(config_pkg, "config", _Boom())
        # Should not raise; falls back to GBP internally (lines 220-221).
        book.print_book_summary([], currency=None)
