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
Runtime data structures for the fire model.

AssetFireFeatures is the CDM-derived feature bundle the initiation stage reads
(the small subset of commercial-asset + resilience fields that drive lambda_i
and the initiation-class prior). IgnitionDraw and AssetInitiationResult capture
the Stage-1 output: per-draw fire/no-fire decisions and per-asset summaries.

Dataclasses are value objects; sampling logic lives in initiation.py.
"""

from ._containment import (
    AssetFireResult,
    ContainmentOutcome,
    IntensityTrack,
    ResponseProfile,
)
from ._features import AssetFireFeatures
from ._initiation import AssetInitiationResult, IgnitionDraw

__all__ = [
    "AssetFireFeatures",
    "IgnitionDraw",
    "AssetInitiationResult",
    "ResponseProfile",
    "IntensityTrack",
    "ContainmentOutcome",
    "AssetFireResult",
]
