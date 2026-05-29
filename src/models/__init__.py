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

#
# Models package - core pricing and simulation models
#
# This package contains standalone models that can be used independently
# or composed together for PRS pricing.

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
