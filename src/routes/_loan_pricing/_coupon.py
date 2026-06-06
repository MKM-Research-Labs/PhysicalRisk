# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Standalone-calculator contractual coupon assembly."""

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


def _build_coupon(term_years: float,
                  credit_rating: str,
                  flood_category: str,
                  wind_category: str,
                  flood_spread_bps: Optional[float] = None,
                  union_spread_bps: Optional[float] = None,
                  prs_spread_bps: Optional[float] = None,
                  prs_scenario: Optional[str] = None) -> Dict[str, Any]:
    """Assemble the contractual coupon from its components.

    ``coupon = risk-free + credit spread + flood spread + wind spread``

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

    # PRS scenario override: one modelled spread drives the whole hazard leg.
    if prs_spread_bps is not None and float(prs_spread_bps) >= 0:
        scenario = (str(prs_scenario).strip().lower() if prs_scenario else "fow")
        total_bps = float(prs_spread_bps)
        total = total_bps / 10000.0
        if scenario == "win":
            # Pure wind frequency — no flood component.
            flood_leg, wind_leg = 0.0, total
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
            flood_leg, wind_leg = total, 0.0
        return {
            "rate": rf + credit + total,
            "risk_free": rf,
            "credit_spread": credit,
            "flood_spread": flood_leg,
            "wind_spread": wind_leg,
            "hazard_spread": total,
            "flood_annual_hazard": total,
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

    return {
        "rate": rf + credit + flood + wind,
        "risk_free": rf,
        "credit_spread": credit,
        "flood_spread": flood,
        "wind_spread": wind,
        "hazard_spread": flood + wind,
        "flood_annual_hazard": annual_hazard,
        "flood_priced_by": flood_source,
        "wind_priced_by": wind_source,
        "credit_rating": (str(credit_rating).strip().upper()
                          if credit_rating else DEFAULT_CREDIT_RATING),
    }
