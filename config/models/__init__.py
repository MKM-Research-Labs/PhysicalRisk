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
Model parameter registry.

All hard-coded analytical parameters for the MKM model library live here.
Grouped by model subsystem. Model source files import from this module
rather than defining constants inline.

Subsections:
    PRS Basis Waterfall       — prs_analytical.py
    Depth-Damage Curve        — floodrisk/depth_damage.py
    Flood Velocity / Manning  — floodrisk/velocity.py
    Property Valuation        — valuation/property_value.py
    Insurance Premium         — valuation/insurance.py
"""

from config.damage import DAMAGE_POINTS, DEPTH_POINTS  # noqa: F401

from config.models._flood import *  # noqa: F401,F403
from config.models._valuation import *  # noqa: F401,F403
from config.models._misc import *  # noqa: F401,F403
