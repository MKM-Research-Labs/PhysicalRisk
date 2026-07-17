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

"""Wind damage-function field chains (RED — feed the PRS wind spread).

Keys are CDM dotted paths from the record root. The wind fields live under the
shared ``ProtectionMeasures`` block, so the same paths apply to residential and
commercial assets. Source of truth: ``src/models/winddamage/cdm.py`` and the
wind vulnerability model (MKM-WD-001).
"""

from .tiers import RED

_WD = "MKM-WD-001 wind damage"
_PRS = "PRS wind spread"

# Shared downstream tail: damage ratio -> PRS wind spread.
_WIND_TAIL = [
    {"node": "bri_wind_damage()", "kind": "function",
     "ref": "src/models/winddamage/vulnerability.py"},
    {"node": "per-event wind damage_ratio", "kind": "output",
     "ref": "src/models/winddamage/event.py"},
    {"node": "PRS wind spread (bps)", "kind": "output",
     "ref": "src/port/src/property/hc/pricing/_wind.py"},
]

WIND_FIELDS = {
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIWindScore": {
        "tier": RED,
        "summary": "Wind resilience score; shifts the damage curve's v_50 upward (a more "
                   "resilient building fails at higher wind), feeding the PRS wind spread.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "BRIWindScore (CDM)", "kind": "field"},
            {"node": "bri_v50_shift()", "kind": "function",
             "ref": "src/models/winddamage/bri_shift.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdMinorMps": {
        "tier": RED,
        "summary": "Damage-onset wind threshold (v_50, m/s); the centre of the wind "
                   "vulnerability sigmoid and the persistence reference level.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdMinorMps (CDM)", "kind": "field"},
            {"node": "resolve_threshold_ms()", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdMajorMps": {
        "tier": RED,
        "summary": "Severe-damage wind threshold; fallback v_50 when the minor threshold "
                   "is absent.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdMajorMps (CDM)", "kind": "field"},
            {"node": "resolve_threshold_ms()", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
    "ProtectionMeasures.HazardProfile.WindThresholdKph": {
        "tier": RED,
        "summary": "Legacy wind threshold (km/h); converted to m/s as the v_50 fallback.",
        "consumers": [_WD, _PRS],
        "chain": [
            {"node": "WindThresholdKph (CDM, legacy)", "kind": "field"},
            {"node": "resolve_threshold_ms()  (÷3.6)", "kind": "function",
             "ref": "src/models/winddamage/threshold.py"},
        ] + _WIND_TAIL,
    },
}
