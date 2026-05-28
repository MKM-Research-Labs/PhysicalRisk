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

"""Threshold resolution — property record → v_50 (m/s) for the damage curve.

The CDM now carries the operational threshold in m/s
(`ProtectionMeasures.HazardProfile.WindThresholdMajorMps`). Legacy records
may still carry `WindThresholdKph` instead — extract_wind_threshold_mps
handles the conversion. This module is the single converter, with a
fallback to the configured default when neither field is present.
"""

from config.damage import DEFAULT_WIND_THRESHOLD_KPH
from models.winddamage.cdm import extract_wind_threshold_mps


__all__ = ["KMH_TO_MS", "kph_to_ms", "resolve_threshold_ms"]


KMH_TO_MS: float = 1.0 / 3.6


def kph_to_ms(value_kph: float) -> float:
    return value_kph * KMH_TO_MS


def resolve_threshold_ms(property_record: dict) -> float:
    """Return the property's operational v_50 in m/s.

    Resolution rule:
        1. CDM field WindThresholdMajorMps present     → use directly
        2. CDM field WindThresholdKph present (legacy) → / 3.6
        3. else                                        → DEFAULT_WIND_THRESHOLD_KPH / 3.6
    """
    mps = extract_wind_threshold_mps(property_record)
    if mps is not None:
        return mps
    return kph_to_ms(DEFAULT_WIND_THRESHOLD_KPH)
