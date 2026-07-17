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
Property-Level Hazard Curve Generator with PRS Pricing and Basis Calculation.

For each property in the propertyts output:
1. Counts severe flood events from the Monte Carlo simulation
2. Computes spread as event_count / num_scenarios (bp)
3. Calculates basis vs synthetic gauge spread
4. Attaches spread decomposition (gauge → SHD → SHE → property)

Usage:
    from port.src.property.hc import PropertyHazardCurveGenerator
    generator = PropertyHazardCurveGenerator(output_dir)
    result = generator.generate()
"""

from ._generator import PropertyHazardCurveGenerator

__all__ = ["PropertyHazardCurveGenerator"]
