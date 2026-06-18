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

"""
Mortgage Portfolio Generator.

This package generates synthetic mortgage data based on the LoanCDM schema.
Mortgages are linked to properties from the property portfolio.

Usage:
    from port.src.mortgage import MortgagePortfolioGenerator, generate_mortgages

    result = generate_mortgages()           # uses config.CATCHMENT
    result = MortgagePortfolioGenerator().generate()
"""

from ._generator import (
    DateTimeEncoder,
    MortgagePortfolioGenerator,
    generate_mortgages,
)

__all__ = ["MortgagePortfolioGenerator", "generate_mortgages", "DateTimeEncoder"]
