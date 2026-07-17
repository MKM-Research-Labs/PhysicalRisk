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

"""Standalone-calculator contractual coupon assembly."""

import math
from typing import Any, Dict, Optional

from config.loan import (
    PRS_FLOOD_RECOVERY,
    credit_spread_for_rating,
    discount_rate,
    flood_annual_hazard,
    wind_hazard_spread,
)
from models.hazard.prs_analytical import compute_prs_spread

from routes._loan_pricing._constants import DEFAULT_CREDIT_RATING


def _truthy(value: Any) -> bool:
    """Interpret a toggle value (bool / number / "true"/"on"/"1") as on/off."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return False


def _peril_leg(spread_bps: Optional[float], include: Any) -> float:
    """Decimal leg for an independent peril — 0.0 when toggled off or absent."""
    if not _truthy(include) or spread_bps is None:
        return 0.0
    try:
        bps = float(spread_bps)
    except (TypeError, ValueError):
        return 0.0
    return bps / 10000.0 if bps >= 0 else 0.0


def _all_in(fw_base: float, *peril_legs: float) -> float:
    """Root-sum-of-squares of the flood/wind basis and the independent peril
    legs — the all-in hazard spread, matching the PRS pricer's coupon."""
    total = fw_base * fw_base
    for leg in peril_legs:
        total += leg * leg
    return math.sqrt(total)


def _build_coupon(term_years: float,
                  credit_rating: str,
                  flood_category: str,
                  wind_category: str,
                  flood_spread_bps: Optional[float] = None,
                  union_spread_bps: Optional[float] = None,
                  prs_spread_bps: Optional[float] = None,
                  prs_scenario: Optional[str] = None,
                  fire_spread_bps: Optional[float] = None,
                  seismic_spread_bps: Optional[float] = None,
                  include_fire: Any = False,
                  include_seismic: Any = False) -> Dict[str, Any]:
    """Assemble the contractual coupon from its components.

    ``coupon = risk-free + credit spread + all-in hazard spread``

    The flood/wind basis (a single correlated waterfall — the menu scenario, or
    the flood+wind category split) forms the base hazard leg. Fire and seismic
    are *independent* perils, toggled on/off by the calculator's binary buttons;
    each toggled leg is folded into the basis by root-sum-of-squares so the loan
    coupon matches the PRS pricer's all-in:

        all-in = sqrt(flood_wind_base^2 + [fire^2] + [seismic^2])

    When both peril toggles are off (or the asset has no fire/seismic leg) the
    all-in reduces to the flood/wind basis, so the coupon is unchanged.

    **PRS scenario override.** When ``prs_spread_bps`` is supplied (the user
    picked a hazard scenario in the calculator's dropdown), that single
    modelled spread *is* the coupon's entire hazard leg and supersedes the
    flood/union split below. ``prs_scenario`` (flo | bri | win | faw | fow | baw | bow)
    only labels the leg and controls how it is shown back as a flood/wind
    decomposition (e.g. ``win`` is all wind; ``fow`` splits into flood plus the
    incremental wind). The total hazard always equals the chosen spread.

    The flood spread is *PRS-priced*. There are two sources, in priority order:

    1. **Asset curve** — when ``flood_spread_bps`` is supplied (the calculator
       was launched from a property/commercial asset and read that asset's own
       modelled flood spread from its hazard curve), it is used verbatim. This
       is the property's simulated flood frequency, so the flood leg matches
       the property PRS pricer exactly (no coarse category bucket).
    2. **Category lookup** — otherwise the flood-risk category maps to an annual
       flood probability which the analytical PRS pricer (``compute_prs_spread``)
       converts to a fair CDS-equivalent spread on the risk-free rate. This is
       the fallback for a truly standalone calculator (no asset) or an asset
       with too few flood events to have a hazard curve.

    The wind spread has two sources, in priority order:

    1. **Asset curve (union)** — when ``union_spread_bps`` (the modelled
       flood-OR-wind PRS spread) is supplied alongside an asset flood spread,
       the wind leg is the *incremental* hazard on top of flood. By
       inclusion-exclusion ``union = flood + wind - joint``, so the incremental
       ``wind = union - flood`` is exactly the genuinely-wind-driven frequency
       (the joint flood-and-wind events are already in the flood leg and are not
       double-counted). The total hazard leg then equals the union spread.
    2. **Category lookup** — otherwise wind has no PRS curve, so it falls back
       to the static wind-category spread (flood-only catchments, or a truly
       standalone calculator).

    Returns the total ``rate`` plus the full decomposition (all decimals).
    """
    rf = discount_rate(term_years)
    credit = credit_spread_for_rating(credit_rating)

    # Independent peril legs (toggled on/off by the calculator's buttons).
    fire_leg = _peril_leg(fire_spread_bps, include_fire)
    seismic_leg = _peril_leg(seismic_spread_bps, include_seismic)
    fire_on = _truthy(include_fire)
    seismic_on = _truthy(include_seismic)

    # PRS scenario override: one modelled spread drives the flood/wind basis.
    if prs_spread_bps is not None and float(prs_spread_bps) >= 0:
        scenario = (str(prs_scenario).strip().lower() if prs_scenario else "fow")
        total_bps = float(prs_spread_bps)
        fw_base = total_bps / 10000.0
        if scenario == "win":
            # Pure wind frequency — no flood component.
            flood_leg, wind_leg = 0.0, fw_base
        elif scenario in ("fow", "bow"):
            # Union splits into flood + incremental wind so the legs still read
            # naturally; the asset flood spread (BRI-preferred) is the base when
            # available, else the whole leg is flood. 'bow' is the same union on
            # the BRI-resilient flood leg, so the same split applies.
            base_bps = (float(flood_spread_bps)
                        if (flood_spread_bps is not None and flood_spread_bps >= 0)
                        else total_bps)
            base_bps = min(base_bps, total_bps)
            flood_leg, wind_leg = base_bps / 10000.0, (total_bps - base_bps) / 10000.0
        else:
            # flo / bri / faw / baw are flood-side scenarios — shown as a flood leg.
            flood_leg, wind_leg = fw_base, 0.0
        all_in = _all_in(fw_base, fire_leg, seismic_leg)
        return {
            "rate": rf + credit + all_in,
            "risk_free": rf,
            "credit_spread": credit,
            "flood_spread": flood_leg,
            "wind_spread": wind_leg,
            "fire_spread": fire_leg,
            "seismic_spread": seismic_leg,
            "fire_included": fire_on,
            "seismic_included": seismic_on,
            "flood_wind_base": fw_base,
            "hazard_spread": all_in,
            "flood_annual_hazard": fw_base,
            "flood_priced_by": "PRS (scenario: %s)" % scenario,
            "wind_priced_by": "PRS (scenario: %s)" % scenario,
            "prs_scenario": scenario,
            "prs_spread_bps": total_bps,
            "credit_rating": (str(credit_rating).strip().upper()
                              if credit_rating else DEFAULT_CREDIT_RATING),
        }

    asset_flood = flood_spread_bps is not None and flood_spread_bps >= 0
    if asset_flood:
        # Asset's own modelled flood spread — recovery is 0 for flood, so the
        # spread is, to first order, the annual flood probability itself.
        flood_bps = float(flood_spread_bps)
        annual_hazard = flood_bps / 10000.0
        flood_source = "PRS (asset curve)"
    else:
        annual_hazard = flood_annual_hazard(flood_category)
        flood_bps = compute_prs_spread(
            annual_hazard_rate=annual_hazard,
            tenor=max(int(round(term_years)), 1),
            recovery=PRS_FLOOD_RECOVERY,
            risk_free_rate=rf,
        )
        flood_source = "PRS (category)"
    flood = flood_bps / 10000.0

    # Wind leg. Only PRS-price it from the union when the flood leg is *also*
    # asset-priced — mixing an asset union against a coarse flood-category leg
    # would compare incompatible scales. union >= flood always holds (the union
    # count >= the flood count), but clamp at 0 defensively.
    if union_spread_bps is not None and union_spread_bps >= 0 and asset_flood:
        wind_bps = max(0.0, float(union_spread_bps) - flood_bps)
        wind = wind_bps / 10000.0
        wind_source = "PRS (asset curve, union)"
    else:
        wind = wind_hazard_spread(wind_category)
        wind_source = "static"

    fw_base = flood + wind
    all_in = _all_in(fw_base, fire_leg, seismic_leg)
    return {
        "rate": rf + credit + all_in,
        "risk_free": rf,
        "credit_spread": credit,
        "flood_spread": flood,
        "wind_spread": wind,
        "fire_spread": fire_leg,
        "seismic_spread": seismic_leg,
        "fire_included": fire_on,
        "seismic_included": seismic_on,
        "flood_wind_base": fw_base,
        "hazard_spread": all_in,
        "flood_annual_hazard": annual_hazard,
        "flood_priced_by": flood_source,
        "wind_priced_by": wind_source,
        "credit_rating": (str(credit_rating).strip().upper()
                          if credit_rating else DEFAULT_CREDIT_RATING),
    }
