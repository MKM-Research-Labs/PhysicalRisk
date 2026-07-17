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
Storm gauge forward model package.

Computes gauge water level responses given storm parameters.

Submodules:
  - data_structures: Enums, Storm, GaugeConfig, GaugeResponse dataclasses
  - forward_model: StormGaugeModel computation engine
  - storm_factory: create_storm(), load_gauges_from_portfolio()
"""

from models.stormgauge.data_structures import (
    DecayKernel,
    GaugeConfig,
    GaugeResponse,
    IntensityProfile,
    Storm,
    TrackPoint,
)
from models.stormgauge.forward_model import StormGaugeModel
from models.stormgauge.storm_factory import create_storm, load_gauges_from_portfolio

__all__ = [
    'IntensityProfile', 'DecayKernel', 'TrackPoint',
    'Storm', 'GaugeConfig', 'GaugeResponse',
    'StormGaugeModel',
    'create_storm', 'load_gauges_from_portfolio',
]
