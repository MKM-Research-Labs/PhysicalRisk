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

"""
Trading Desk startup preloader.

When the Pi button is clicked, shows a progress popup listing all datasets
being fetched in parallel.  Each row gets a tick (✓) when its fetch
resolves.  Once all fetches settle, the popup closes and the main panel
opens with pre-populated data.

Datasets preloaded (stored on window._td* variables):
  _tdPreBlotter      — /api/v1/trading/blotter
  _tdPreMarket       — /api/v1/trading/market-state
  _tdPreGauges       — /api/v1/gauges
  _tdPreStressStorms — /api/v1/trading/stress/storms
  _tdPrePortStorms   — /api/v1/trading/stress/portfolio-storms
  _tdPreEodHistory   — /api/v1/trading/eod/history
  _tdPreYieldCurve   — /api/v1/trading/yield-curve
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return the JS fragment for the preloader popup and prefetch logic."""
    return js_static('trading/preloader.js')
