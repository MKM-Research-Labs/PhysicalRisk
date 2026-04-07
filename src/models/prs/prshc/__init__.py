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
Physical Risk Swap (PRS) Pricing with Flood Hazard Curves.

This package demonstrates how to use the hazard curve output from
hazard_curve.py to price a Physical Risk Swap using QuantLib's
CDS pricing framework.

The key insight is that flood risk can be modeled like credit risk:
- Survival probability S(t) = P(no flood by time t)
- Default probability = P(at least one flood by time t)
- Hazard rate lambda = annual flood probability (Poisson intensity)

Usage:
    python3 -m models.prs.prshc.cli --gauge THAMES-G001 --trigger warning
    python3 -m models.prs.prshc.cli --hazard-file input/thames/hazard_curves.json
"""

from .curves import create_survival_curve_from_hazard, create_flat_hazard_curve
from .pricer import price_prs
from .io import load_hazard_curves, print_pricing_results
from .cli import main

__all__ = [
    'create_survival_curve_from_hazard',
    'create_flat_hazard_curve',
    'price_prs',
    'load_hazard_curves',
    'print_pricing_results',
    'main',
]
