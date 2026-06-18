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

"""Coverage tests for port.src.book.book — the no-real-curves guard and the
print_book_summary currency fallback. (The REIT-skip line needs full book
generation and is left for a later tranche.)"""

import json

import pytest

from port.src.book import book


def _write(path, obj):
    path.write_text(json.dumps(obj))


class TestBookGuards:
    def test_raises_when_only_synthetic_curves(self, tmp_path):
        gaugehc = tmp_path / "gaugehc.json"
        _write(gaugehc, {"hazard_curves": {"SYNTH-1": {}, "SYNTH-2": {}}})
        with pytest.raises(ValueError, match="non-SYNTH"):
            book.generate_market_making_book(
                gaugehc_path=gaugehc,
                counterparty_path=tmp_path / "counterparty.json",
                output_dir=tmp_path,
            )  # line 121

    def test_print_book_summary_currency_falls_back_to_gbp(self, monkeypatch):
        import config as config_pkg

        class _Boom:
            @property
            def CURRENCY(self):
                raise RuntimeError("no config")

        monkeypatch.setattr(config_pkg, "config", _Boom())
        # Should not raise; falls back to GBP internally (lines 220-221).
        book.print_book_summary([], currency=None)
