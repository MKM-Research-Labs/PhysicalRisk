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

"""Pipeline helper utilities."""

import numpy as np


def _extract_pulse_peaks(levels: np.ndarray, seq, lag: int = 2) -> list:
    """Extract per-pulse peak levels from a 168h gauge hydrograph.

    For each storm in the sequence, finds the maximum level within the
    storm's active window (start -> start + duration + lag + 6h buffer).

    Returns a list of dicts, one per pulse, with keys:
        storm_index, peak_m, start_hour, duration_hours, precip_mm
    """
    n = len(levels)
    result = []
    for storm in seq.storms:
        start_h = max(0, int(round(storm.start_time_hours)))
        end_h = min(n, start_h + int(round(storm.duration_hours)) + lag + 6)
        if start_h >= end_h:
            continue
        window = levels[start_h:end_h]
        peak_m = float(np.max(window))
        result.append({
            "storm_index": storm.storm_index,
            "peak_m": round(peak_m, 3),
            "start_hour": round(storm.start_time_hours, 1),
            "duration_hours": round(storm.duration_hours, 1),
            "precip_mm": round(storm.precipitation_mm, 1),
        })
    return result
