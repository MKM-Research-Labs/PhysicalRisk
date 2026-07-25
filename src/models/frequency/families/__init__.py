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

"""Distribution families for the Event Frequency Model (MKM-EF-001, Stage 2).

Poisson and Negative Binomial, and a small-sample-aware selector between them.
Per rule R4 this module contains no function definitions — only re-exports.
"""

from ._negbin import NegBinFit, fit_negbin
from ._poisson import PoissonFit, fit_poisson
from ._select import (
    DispersionTest,
    FamilySelection,
    OVER_DISPERSED,
    POISSON_CONSISTENT,
    UNDER_DISPERSED,
    dispersion_test,
    select_family,
    selection_to_dict,
)

__all__ = [
    "fit_poisson",
    "PoissonFit",
    "fit_negbin",
    "NegBinFit",
    "dispersion_test",
    "select_family",
    "selection_to_dict",
    "DispersionTest",
    "FamilySelection",
    "OVER_DISPERSED",
    "POISSON_CONSISTENT",
    "UNDER_DISPERSED",
]
