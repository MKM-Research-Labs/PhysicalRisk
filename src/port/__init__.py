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
