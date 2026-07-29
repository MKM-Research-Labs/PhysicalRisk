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
Portfolio Generators Package.

Contains catchment-agnostic portfolio generators that delegate
random value generation to catchment-specific modules in port.random.

All generators use config.py for:
- Path resolution (no path manipulation in modules)
- Catchment-specific module loading
- Output directory configuration

Structure:
    port/src/
    ├── gauge_portfolio.py       - Flood gauge portfolio generator
    ├── property_portfolio.py    - Property portfolio generator
    ├── mortgage_portfolio.py    - Mortgage portfolio generator
    ├── gaugetseries_portfolio.py - Gauge time series generator
    └── stormtseries_portfolio.py - Storm time series generator

Usage:
    # Catchment is pinned globally by the CLI entry point (phys.py port
    # --thames / --halong, or `config.catchment_id = "halong"` from
    # tests). Generators just read config.catchment_id; they never
    # mutate it.
    from port.src import generate_gauges, generate_properties

    result = generate_gauges(count=40)
    result = generate_properties(count=200)

    # Or use generator classes directly
    from port.src import GaugePortfolioGenerator

    generator = GaugePortfolioGenerator()
    result = generator.generate(count=40)
"""

from .gauge import GaugePortfolioGenerator, generate_gauges
from .gauge.gaugets import GaugeTimeSeriesGenerator, generate_gaugets
from .mortgage import MortgagePortfolioGenerator, generate_mortgages
from .property import PropertyPortfolioGenerator, generate_properties

__all__ = [
    # Generator classes
    'GaugePortfolioGenerator',
    'PropertyPortfolioGenerator',
    'MortgagePortfolioGenerator',
    'GaugeTimeSeriesGenerator',

    # Convenience functions (use config.CATCHMENT)
    'generate_gauges',
    'generate_properties',
    'generate_mortgages',
    'generate_gaugets',
]
