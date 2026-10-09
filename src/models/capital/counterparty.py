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

"""Counterparty capital: SA-CCR, BA-CVA (reduced) and SA risk weights.

Shared by MKM-CR-001 and MKM-XV-001 (D-07). Every function takes numpy arrays
and broadcasts, so the XVA model can evaluate it in every Monte Carlo state at
once (Green §13.4: capital as a payout). Paragraph references are to the Basel
Framework (CRE52, MAR50, CRE20).
"""

from typing import Dict, Sequence

import numpy as np

from config.counterparty_capital import (
    BA_CVA_CORRELATION,
    BA_CVA_DISCOUNT_SCALAR,
    BA_CVA_MATURITY_FLOOR_YEARS,
    BA_CVA_RW,
    BA_CVA_SD_RATE,
    INVESTMENT_GRADE,
    SA_RW_BANK,
    SA_RW_CORPORATE,
    SACCR_ALPHA,
    SACCR_DAYS_PER_YEAR,
    SACCR_MIN_MATURITY_DAYS,
    SACCR_MULTIPLIER_FLOOR,
    SACCR_SD_RATE,
)


def letter_grade(rating: str) -> str:
    """'BBB-' -> 'BBB', 'A+' -> 'A'; anything not rated by letter -> 'unrated'."""
    core = (rating or "").strip().upper().rstrip("+-")
    return core if core in ("AAA", "AA", "A", "BBB", "BB", "B", "CCC") else "unrated"


def sa_risk_weight(rating: str, exposure_class: str = "corporate") -> float:
    table = {"corporate": SA_RW_CORPORATE, "bank": SA_RW_BANK}[exposure_class]
    return table[letter_grade(rating)]


# --- SA-CCR ------------------------------------------------------------------

def supervisory_duration(start, end):
    """SD = (exp(-0.05 S) - exp(-0.05 E)) / 0.05, S and E in years (CRE52.34)."""
    start, end = np.maximum(start, 0.0), np.asarray(end, dtype=float)
    return (np.exp(-SACCR_SD_RATE * start) - np.exp(-SACCR_SD_RATE * end)) / SACCR_SD_RATE


def maturity_factor_unmargined(maturity):
    """sqrt(min(M, 1) / 1 year), M floored at 10 business days (CRE52.48)."""
    floor = SACCR_MIN_MATURITY_DAYS / SACCR_DAYS_PER_YEAR
    return np.sqrt(np.minimum(np.maximum(maturity, floor), 1.0))


def maturity_factor_margined(mpor_days: float) -> float:
    """1.5 sqrt(MPoR / 1 year), MPoR in business days (CRE52.52)."""
    return 1.5 * np.sqrt(mpor_days / SACCR_DAYS_PER_YEAR)


def aggregate_addon(addons: Sequence[np.ndarray], correlation) -> np.ndarray:
    """[(sum rho_k A_k)^2 + sum (1 - rho_k^2) A_k^2]^1/2 over entities or types.

    ``correlation`` is one rho for all or one per add-on (credit indices use
    0.8, single names 0.5). The add-ons are signed, so long and short positions
    offset in the systematic term only (BCBS 279 Annex 4a, Example 2).
    """
    stack = np.stack([np.asarray(a, dtype=float) for a in addons])
    rho = np.broadcast_to(np.asarray(correlation, dtype=float).reshape(
        (-1,) + (1,) * (stack.ndim - 1)), stack.shape)
    systematic = (rho * stack).sum(axis=0) ** 2
    idiosyncratic = ((1.0 - rho ** 2) * stack ** 2).sum(axis=0)
    return np.sqrt(systematic + idiosyncratic)


def commodity_addon(hedging_sets: Dict[str, Dict[str, np.ndarray]],
                    factors: Dict[str, float], correlation: float) -> np.ndarray:
    """Sum over hedging sets of the aggregated commodity-type add-ons (CRE52.69-71).

    ``hedging_sets`` maps hedging set -> commodity type -> signed effective
    notional; ``factors`` gives each hedging set's supervisory factor.
    """
    total = 0.0
    for hedging_set, types in hedging_sets.items():
        addons = [factors[hedging_set] * notional for notional in types.values()]
        total = total + aggregate_addon(addons, correlation)
    return np.asarray(total, dtype=float)


def pfe_multiplier(value, collateral, addon):
    """min(1, floor + (1 - floor) exp((V - C) / (2 (1 - floor) AddOn))) (CRE52.23)."""
    value, collateral, addon = np.broadcast_arrays(
        np.asarray(value, float), np.asarray(collateral, float), np.asarray(addon, float))
    f = SACCR_MULTIPLIER_FLOOR
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        raw = f + (1.0 - f) * np.exp((value - collateral) / (2.0 * (1.0 - f) * addon))
    return np.where(addon > 0, np.minimum(1.0, raw), 1.0)


def replacement_cost(value, collateral, margined: bool = False, threshold: float = 0.0,
                     mta: float = 0.0, nica=0.0):
    """Unmargined max(V - C, 0); margined max(V - C, TH + MTA - NICA, 0) (CRE52.10-18)."""
    rc = np.maximum(np.asarray(value) - collateral, 0.0)
    if margined:
        rc = np.maximum(rc, threshold + mta - np.asarray(nica))
    return rc


def ead(value, collateral, addon, margined: bool = False, threshold: float = 0.0,
        mta: float = 0.0, nica=0.0, unmargined_addon=None):
    """EAD = alpha (RC + multiplier x AddOn). A margined set is capped at its
    unmargined EAD (CRE52.2), for which ``unmargined_addon`` is needed."""
    rc = replacement_cost(value, collateral, margined, threshold, mta, nica)
    out = SACCR_ALPHA * (rc + pfe_multiplier(value, collateral, addon) * addon)
    if margined:
        if unmargined_addon is None:
            raise ValueError("a margined EAD needs the unmargined add-on for its cap")
        cap = ead(value, collateral, unmargined_addon)   # same netting set, same collateral
        out = np.minimum(out, cap)
    return out


# --- BA-CVA, reduced (MAR50.14-16) -------------------------------------------

def ba_cva_risk_weight(sector: str, rating: str) -> float:
    ig, hy = BA_CVA_RW[sector]
    return ig if letter_grade(rating) in INVESTMENT_GRADE else hy


def ba_cva_discount(maturity):
    """DF_NS = (1 - exp(-0.05 M)) / (0.05 M), and 1 at M = 0."""
    m = np.asarray(maturity, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        df = -np.expm1(-BA_CVA_SD_RATE * m) / (BA_CVA_SD_RATE * m)
    return np.where(m > 0, df, 1.0)


def ba_cva_maturity(maturities: Sequence[np.ndarray], notionals: Sequence[np.ndarray]):
    """Notional-weighted remaining maturity of the live trades, floored (CRE32.47)."""
    m, n = np.stack(maturities), np.stack(notionals)
    total = n.sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        weighted = np.where(total > 0, (m * n).sum(axis=0) / total, 0.0)
    return np.where(total > 0, np.maximum(weighted, BA_CVA_MATURITY_FLOOR_YEARS), 0.0)


def ba_cva_reduced(scva_by_counterparty: Dict[str, np.ndarray]) -> np.ndarray:
    """K_reduced = [(rho sum SCVA)^2 + (1 - rho^2) sum SCVA^2]^1/2, times DS."""
    stack = np.stack(list(scva_by_counterparty.values()))
    k = np.sqrt((BA_CVA_CORRELATION * stack.sum(axis=0)) ** 2
                + (1.0 - BA_CVA_CORRELATION ** 2) * (stack ** 2).sum(axis=0))
    return BA_CVA_DISCOUNT_SCALAR * k


def scva(risk_weight: float, ead_ns, maturity_ns):
    """SCVA_c = RW_c M_NS EAD_NS DF_NS / alpha, for one netting set."""
    return risk_weight * maturity_ns * ead_ns * ba_cva_discount(maturity_ns) / SACCR_ALPHA
