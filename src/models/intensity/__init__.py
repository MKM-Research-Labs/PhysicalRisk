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
Storm Intensity Distribution package.

Hybrid normal-Pareto distribution with controllable tail behaviour
for PRS storm intensity modelling.

Usage:
    from models.intensity import IntensityDistribution, DistributionParameters
    from models.intensity import SCENARIO_FAMILIES, compare_scenarios
"""

from .cli import compare_scenarios, main
from .distribution import IntensityDistribution
from .parameters import SCENARIO_FAMILIES, DistributionParameters

__all__ = [
    "DistributionParameters",
    "SCENARIO_FAMILIES",
    "IntensityDistribution",
    "compare_scenarios",
    "main",
]
