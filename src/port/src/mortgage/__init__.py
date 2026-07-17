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
