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
MKM Models Package

Available models:
- intensity: Storm intensity distribution with controllable tails
- stormgauge: Forward model mapping storms to gauge responses
- hazard: Hazard curve building, GEV fitting, and QuantLib pricing
- floodrisk: Depth-damage, spatial, velocity, risk analytics
- statistics: Timeseries analysis and synthetic generation
- risk: Risk assessment and scoring
- valuation: Property valuation and insurance
- loan: Loan pricing and credit risk
- prs: Physical Risk Swap pricing (QuantLib CDS)

Usage:
    from models.intensity import IntensityDistribution
    from models.stormgauge import StormGaugeModel, create_storm
    from models.hazard import HazardCurveBuilder, build_hazard_curves
"""

# Explicit imports only - don't scan the folder
__all__ = [
    'intensity',
    'stormgauge',
    'hazard',
    'floodrisk',
    'statistics',
    'risk',
    'valuation',
    'loan',
    'prs',
]
