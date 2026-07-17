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

"""Internal value-mapping helpers for the OED exporter."""

from typing import Dict, Optional

from port.cdm.oed_export._lookups import (
    _HAZARD_ACTIVE_CLASSES,
    _HAZARD_OASIS_CODE,
)


def _currency() -> str:
    """ISO 4217 currency code for the active catchment (OED LocCurrency).

    Function-local import keeps oed_export importable without forcing a
    config load at module import time. Falls back to GBP defensively.
    """
    try:
        from config import config
        return config.CURRENCY
    except Exception:
        return "GBP"


def _lookup(table: Dict[str, int], key: Optional[str], default: int = 0) -> int:
    if key is None:
        return default
    return table.get(key, default)


def _lookup_str(table: Dict[str, str], key: Optional[str], default: str = "") -> str:
    if key is None:
        return default
    return table.get(key, default)


def _perils_covered(hazard_profile: dict) -> str:
    """Build the OED LocPerilsCovered string from CDM HazardProfile.

    WF (flood) is always included unless FloodHazardClass is explicitly None —
    this is a flood risk platform and every property is subject to flood modelling.
    All other perils require Medium or above to be included.
    """
    active = []
    flood_class = hazard_profile.get("FloodHazardClass")
    if flood_class not in (None, "None", ""):
        active.append("WF")
    for cdm_field, oasis_code in _HAZARD_OASIS_CODE.items():
        if oasis_code == "WF":
            continue
        val = hazard_profile.get(cdm_field)
        if val and val in _HAZARD_ACTIVE_CLASSES:
            active.append(oasis_code)
    return ";".join(active) if active else "WF"


def _street_address(location: dict) -> str:
    parts = [
        location.get("BuildingNumber", ""),
        location.get("StreetName", ""),
    ]
    return " ".join(p for p in parts if p).strip()


def _bri_user_defs(governing: dict, ref_gauges: list) -> dict:
    """Pack BRI fields into OED LocUserDef slots 1–5."""
    sub_scores = "|".join(str(governing.get(f"BRI{h}Score", "")) for h in ("Flood", "Wind", "Fire", "Seismic"))
    sub_ratings = "|".join(governing.get(f"BRI{h}Rating", "N/A") for h in ("Flood", "Wind", "Fire", "Seismic"))
    gauges = "|".join(ref_gauges[:3]) if ref_gauges else ""
    return {
        "LocUserDef1": governing.get("BRIRating", ""),
        "LocUserDef2": str(round(governing.get("BRIScore", 0.0), 4)),
        "LocUserDef3": sub_scores,
        "LocUserDef4": sub_ratings,
        "LocUserDef5": gauges,
    }
