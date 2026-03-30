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
Re-export shim — hazard code has moved to models.hazard package.
"""

from models.hazard import (
    GaugeHazardCurve,
    GaugeResponse,
    GaugeResponseModel,
    GEVFitter,
    HazardCurveBuilder,
    HazardCurvePoint,
    TermStructurePoint,
    build_hazard_curves,
    compute_term_structure,
    load_gauges,
    load_storms,
    load_storms_from_sequences,
    save_gauge_storm_responses,
    save_hazard_curves,
)

__all__ = [
    "GaugeResponse",
    "HazardCurvePoint",
    "TermStructurePoint",
    "GaugeHazardCurve",
    "GaugeResponseModel",
    "GEVFitter",
    "compute_term_structure",
    "HazardCurveBuilder",
    "load_storms",
    "load_storms_from_sequences",
    "load_gauges",
    "save_hazard_curves",
    "save_gauge_storm_responses",
    "build_hazard_curves",
]
