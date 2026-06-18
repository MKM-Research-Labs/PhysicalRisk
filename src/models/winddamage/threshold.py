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


__all__ = ["KMH_TO_MS", "kph_to_ms", "resolve_threshold_ms", "is_prs_wind"]


KMH_TO_MS: float = 1.0 / 3.6


def kph_to_ms(value_kph: float) -> float:
    return value_kph * KMH_TO_MS


def is_prs_wind(wind: dict) -> bool:
    """True if the paired typhoon's wind counts toward PRS pricing.

    Damage-onset trigger: the property's peak sustained wind for the event
    reached or exceeded its BRI-adjusted operational damage threshold
    (``peak_sustained_ms >= v_50_eff_ms``). ``v_50_eff_ms`` is the raw
    operational ``threshold_ms`` translated by the property's resilience
    (``v_50_eff = threshold_ms + bri_v50_shift(...)``, see
    ``winddamage/bri_shift.py``): a resilient (high-BRI) building carries a
    higher effective threshold, so it fires less readily than a low-BRI
    building exposed to the same wind. Wind-without-flood is therefore
    possible, and how often it happens is governed by where the BRI-adjusted
    exceedance sits relative to the storm's coupled wind.

    Falls back to the raw ``threshold_ms`` when ``v_50_eff_ms`` is absent
    (e.g. legacy damage rows written before the effective-threshold field
    was added).

    Binary by design: PRS is a frequency / event-count payout, NOT the
    continuous wind damage amount (that is the insurance-loss view served by
    the wind-impact route, which must not feed the spread).

    ``wind`` is one per-property row from ``typhoon/damage/EVT-*.json`` and
    must carry ``peak_sustained_ms`` and either ``v_50_eff_ms`` or the legacy
    ``threshold_ms``.
    """
    peak = wind.get("peak_sustained_ms")
    thr = wind.get("v_50_eff_ms")
    if thr is None:
        thr = wind.get("threshold_ms")
    if peak is None or thr is None:
        return False
    try:
        return float(peak) >= float(thr)
    except (TypeError, ValueError):
        return False


def resolve_threshold_ms(property_record: dict) -> float:
    """Return the property's operational v_50 in m/s.

    Resolution rule (see extract_wind_threshold_mps):
        1. CDM field WindThresholdMinorMps present     → use directly (damage-onset)
        2. CDM field WindThresholdMajorMps present     → use directly (severe fallback)
        3. CDM field WindThresholdKph present (legacy) → / 3.6
        4. else                                        → DEFAULT_WIND_THRESHOLD_KPH / 3.6
    """
    mps = extract_wind_threshold_mps(property_record)
    if mps is not None:
        return mps
    return kph_to_ms(DEFAULT_WIND_THRESHOLD_KPH)
