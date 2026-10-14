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

"""Switch the XVA model's automatic hooks off for the suite (MKM-XV-001).

In production a committed PRS trade reruns its netting set and the port
pipeline runs XVA on the new book (``config.xva.XVA_ON_TRADE_COMMIT``,
``XVA_IN_PORT``). Tests that are not about XVA would each pay for a Monte
Carlo run, so both are off here; the tests that are about them turn them on.
"""

import pytest


@pytest.fixture(autouse=True)
def xva_hooks_off(monkeypatch):
    import config.xva as xva_config
    monkeypatch.setattr(xva_config, "XVA_ON_TRADE_COMMIT", False)
    monkeypatch.setattr(xva_config, "XVA_IN_PORT", False)
