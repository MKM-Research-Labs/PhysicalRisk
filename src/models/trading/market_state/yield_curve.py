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

"""Yield curve management mixin."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class YieldCurveMixin:
    """Manages the risk-free yield curve."""

    def get_yield_rate(self, state: Dict, tenor: int) -> float:
        """Get yield rate for a given tenor from the yield curve."""
        curve = state.get('yield_curve', {})
        rate = curve.get(str(tenor))
        if rate is not None:
            return rate
        # Linear interpolation for non-integer tenors
        keys = sorted(int(k) for k in curve.keys())
        if not keys:
            return state.get('risk_free_rate', 0.04)
        if tenor <= keys[0]:
            return curve[str(keys[0])]
        if tenor >= keys[-1]:
            return curve[str(keys[-1])]
        for i in range(len(keys) - 1):
            if keys[i] <= tenor <= keys[i + 1]:
                t0, t1 = keys[i], keys[i + 1]
                r0, r1 = curve[str(t0)], curve[str(t1)]
                return r0 + (r1 - r0) * (tenor - t0) / (t1 - t0)
        return state.get('risk_free_rate', 0.04)

    def update_yield_curve(self, tenor: int, rate: float) -> Dict:
        """Update a single point on the yield curve."""
        state = self.load()
        if 'yield_curve' not in state:
            state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        state['yield_curve'][str(tenor)] = round(rate, 6)
        self._save(state)
        logger.info("Yield curve updated: %dY = %.4f", tenor, rate)
        return state

    def commit_yield_curve(self, rates: Dict) -> Dict:
        """Commit a full yield curve in one save.

        Args:
            rates: Dict mapping tenor (str) to rate (float), e.g. {'1': 0.035}

        Returns:
            Updated market state
        """
        state = self.load()
        if 'yield_curve' not in state:
            state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        for tenor_str, rate in rates.items():
            state['yield_curve'][str(tenor_str)] = round(float(rate), 6)
        self._save(state)
        logger.info("Yield curve committed (%d tenors)", len(rates))
        return state

    def reset_yield_curve(self) -> Dict:
        """Reset yield curve to default."""
        state = self.load()
        state['yield_curve'] = dict(self.DEFAULT_YIELD_CURVE)
        self._save(state)
        logger.info("Yield curve reset to default")
        return state
