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
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
    from config import config

    # Set catchment (determines which random/params modules to use)
    config.CATCHMENT = "thames"

    # Use convenience functions
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
