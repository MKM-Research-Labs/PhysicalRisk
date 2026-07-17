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

"""Enumerations for the seismic model configuration."""

from enum import Enum


class DamageState(Enum):
    """The four HAZUS/GEM-style damage states of the fragility chain.

    The integer value is the threshold index: DS0 is the no-collapse floor,
    DS3 (complete / collapse) is the point-of-no-return analogue whose
    frequency the PRS pricer charges as the seismic spread.
    """
    DS0 = 0  # None / Slight
    DS1 = 1  # Moderate
    DS2 = 2  # Extensive
    DS3 = 3  # Complete / collapse


class SoilClass(Enum):
    """Eurocode 8 site classes derived from V_S30 (Appendix C2)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
