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

"""Data structures for the Event Frequency Model (MKM-EF-001).

Per rule R4 this module contains no function definitions — only re-exports.
"""

from ._catalogue import EventCatalogue
from ._diagnostics import PotDiagnostics
from ._extraction import Peak, PotExtraction
from ._frame import EventFrame
from ._provenance import CalibrationProvenance, ProvenanceClass
from ._rate import FittedRate
from ._simulation import EventDraws, YearSimulation

__all__ = [
    "EventCatalogue",
    "EventFrame",
    "PotDiagnostics",
    "Peak",
    "PotExtraction",
    "CalibrationProvenance",
    "ProvenanceClass",
    "FittedRate",
    "EventDraws",
    "YearSimulation",
]
