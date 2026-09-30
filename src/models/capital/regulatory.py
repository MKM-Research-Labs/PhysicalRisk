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

"""Rating master scale and the Basel IRB corporate risk weight."""

import math
from typing import Tuple

from scipy.stats import norm

from config.capital import (
    IRB_CONFIDENCE,
    IRB_CORRELATION_DECAY,
    IRB_CORRELATION_MAX,
    IRB_CORRELATION_MIN,
    IRB_MATURITY_A,
    IRB_MATURITY_B,
    IRB_MATURITY_REFERENCE,
    IRB_MATURITY_SLOPE,
    IRB_PD_FLOOR,
    IRB_RW_MULTIPLIER,
    MASTER_SCALE,
)


def irb_corporate_rw(pd: float, lgd: float, m: float) -> float:
    """Basel IRB corporate risk weight (no SME adjustment), as a fraction.

    ``pd`` is a one-year PD, which is what the formula is defined on. PD 1%,
    LGD 45%, M 2.5 gives 92.32%, the Basel reference value.
    """
    pd = max(pd, IRB_PD_FLOOR)
    e = math.exp(-IRB_CORRELATION_DECAY * pd)
    w = (1.0 - e) / (1.0 - math.exp(-IRB_CORRELATION_DECAY))
    r = IRB_CORRELATION_MIN * w + IRB_CORRELATION_MAX * (1.0 - w)
    b = (IRB_MATURITY_A - IRB_MATURITY_B * math.log(pd)) ** 2
    k = lgd * norm.cdf((norm.ppf(pd) + math.sqrt(r) * norm.ppf(IRB_CONFIDENCE))
                       / math.sqrt(1.0 - r)) - pd * lgd
    k *= (1.0 + (m - IRB_MATURITY_REFERENCE) * b) / (1.0 - IRB_MATURITY_SLOPE * b)
    return IRB_RW_MULTIPLIER * k


def grade_for_pd(pd: float) -> Tuple[str, float]:
    """``(grade, SA corporate risk weight)`` for a one-year PD on the master scale."""
    for grade, upper, sa_rw in MASTER_SCALE:
        if pd <= upper:
            return grade, sa_rw
    raise ValueError(f"PD {pd} outside master scale")
