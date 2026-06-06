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
