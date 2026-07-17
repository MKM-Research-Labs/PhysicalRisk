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

"""Runtime types for the seismic model (MKM-SEIS-001).

One module per model stage so each value type lives beside the others it is
produced with:

- ``_features``     — AssetSeismicFeatures (CDM-derived input bundle)
- ``_occurrence``   — EarthquakeEvent, OccurrenceResult (Model A)
- ``_groundmotion`` — GroundMotionSample, GroundMotionResult (Model B)
- ``_response``     — SeismicResponseProfile (Model C)
- ``_damage``       — DamageOutcome, AssetSeismicResult (Model D)
"""

from models.seismic.datastructures._damage import AssetSeismicResult, DamageOutcome
from models.seismic.datastructures._features import AssetSeismicFeatures
from models.seismic.datastructures._groundmotion import (
    GroundMotionResult,
    GroundMotionSample,
)
from models.seismic.datastructures._occurrence import EarthquakeEvent, OccurrenceResult
from models.seismic.datastructures._response import SeismicResponseProfile

__all__ = [
    "AssetSeismicFeatures",
    "EarthquakeEvent",
    "OccurrenceResult",
    "GroundMotionSample",
    "GroundMotionResult",
    "SeismicResponseProfile",
    "DamageOutcome",
    "AssetSeismicResult",
]
