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
Wind damage model — per-property damage ratio from peak sustained wind.

Mirrors the flood damage architecture (scalar curve + BRI-aware wrapper).
Consumes per-event windts from MKM-TC-001 and CDM resilience fields.

Submodules:
    vulnerability.py  scalar_peak_damage(v), bri_peak_damage(v, threshold, ...)
    bri_shift.py      bri_v50_shift(bri_wind, bri_composite)
    cdm.py            property-record navigation (id, threshold, BRI scores)
    threshold.py      WindThresholdMajorMps -> v_50 (m/s), legacy WindThresholdKph alias, default fallback
    extraction.py     load windts/EVT-NNNN.json -> per-property peak winds
    event.py          per-event composer: windts + portfolio -> damage JSON
"""

from models.winddamage.bri_shift import bri_v50_shift
from models.winddamage.cdm import (
    extract_bri_scores,
    extract_lon_lat,
    extract_property_id,
    extract_wind_threshold_kph,
)
from models.winddamage.event import (
    build_event_damage,
    run_event,
    run_event_directory,
)
from models.winddamage.extraction import EventWindts, load_event_peaks
from models.winddamage.threshold import KMH_TO_MS, kph_to_ms, resolve_threshold_ms
from models.winddamage.vulnerability import bri_peak_damage, scalar_peak_damage


__all__ = [
    # vulnerability
    "scalar_peak_damage",
    "bri_peak_damage",
    "bri_v50_shift",
    # cdm navigation
    "extract_property_id",
    "extract_wind_threshold_kph",
    "extract_bri_scores",
    "extract_lon_lat",
    # threshold resolution
    "KMH_TO_MS",
    "kph_to_ms",
    "resolve_threshold_ms",
    # extraction
    "EventWindts",
    "load_event_peaks",
    # event composer
    "build_event_damage",
    "run_event",
    "run_event_directory",
]
