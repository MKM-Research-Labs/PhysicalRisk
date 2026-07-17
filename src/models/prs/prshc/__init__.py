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
