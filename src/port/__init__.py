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
Port Package - Portfolio Generation.

This package contains:
- src/: Catchment-agnostic portfolio generators
- random/: Catchment-specific random value generators
- params/: Catchment-specific parameters
- cdm/: Common Data Model schemas (if separate from root)

Usage:
    from port.src import generate_gauges, generate_properties, generate_mortgages

    result = generate_gauges(count=40)
    result = generate_properties(count=200)
    result = generate_mortgages()
"""

from .src import (
    GaugePortfolioGenerator,
    GaugeTimeSeriesGenerator,
    MortgagePortfolioGenerator,
    PropertyPortfolioGenerator,
    generate_gauges,
    generate_gaugets,
    generate_mortgages,
    generate_properties,
)

__all__ = [
    # Generator classes
    'GaugePortfolioGenerator',
    'PropertyPortfolioGenerator',
    'MortgagePortfolioGenerator',
    'GaugeTimeSeriesGenerator',

    # Convenience functions
    'generate_gauges',
    'generate_properties',
    'generate_mortgages',
    'generate_gaugets',
]
