# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Delta engine pricer functions — risky annuity, gauge delta, basis delta, MTM."""

import math
from typing import Dict

from config.port import BUMP_1BP
from models.hazard.prs_analytical import compute_prs_spread, interpolate_yield_rate


def compute_risky_annuity(annual_hazard_rate: float, tenor: int,
                          risk_free_rate: float = 0.03,
                          yield_curve: dict = None) -> float:
    """
    Compute risky annuity = sum of dt * S(t) * DF(t) for quarterly periods.

    Args:
        annual_hazard_rate: Annual flood probability (0-1)
        tenor: Maturity in years
        risk_free_rate: Continuous risk-free rate
        yield_curve: Optional yield curve dict for tenor-matched discounting

    Returns:
        Risky annuity (float)
    """
    dt = 0.25

    if annual_hazard_rate <= 0:
        annuity = 0.0
        for i in range(1, tenor * 4 + 1):
            t = i * dt
            rf = interpolate_yield_rate(yield_curve, t, risk_free_rate) if yield_curve else risk_free_rate
            annuity += dt * math.exp(-rf * t)
        return annuity

    hazard_lambda = -math.log(1.0 - min(annual_hazard_rate, 0.999))
    annuity = 0.0
    for i in range(1, tenor * 4 + 1):
        t = i * dt
        survival = math.exp(-hazard_lambda * t)
        rf = interpolate_yield_rate(yield_curve, t, risk_free_rate) if yield_curve else risk_free_rate
        discount = math.exp(-rf * t)
        annuity += dt * survival * discount

    return annuity


def compute_gauge_delta(annual_hazard_rate: float, tenor: int,
                        notional: float, recovery: float = 0.0,
                        risk_free_rate: float = 0.03,
                        yield_curve: dict = None) -> Dict:
    """
    Compute gauge delta (DV01): P&L for a 1bp bump in annual hazard rate.

    DV01 = (spread(lambda+1bp) - spread(lambda)) / 10000 * annuity * notional

    Args:
        annual_hazard_rate: Current annual flood probability
        tenor: Remaining maturity in years
        notional: Trade notional in GBP
        recovery: Recovery rate (0-1)
        risk_free_rate: Continuous risk-free rate
        yield_curve: Optional yield curve for tenor-matched discounting

    Returns:
        Dict with delta_spread_bps, dv01_gbp, risky_annuity
    """
    spread_base = compute_prs_spread(
        annual_hazard_rate, tenor, recovery, risk_free_rate,
        yield_curve=yield_curve)
    spread_bumped = compute_prs_spread(
        annual_hazard_rate + BUMP_1BP, tenor, recovery, risk_free_rate,
        yield_curve=yield_curve)

    delta_spread_bps = spread_bumped - spread_base
    risky_annuity = compute_risky_annuity(
        annual_hazard_rate, tenor, risk_free_rate, yield_curve)

    dv01 = (delta_spread_bps / 10000) * risky_annuity * notional

    return {
        'delta_spread_bps': round(delta_spread_bps, 4),
        'dv01_gbp': round(dv01, 2),
        'risky_annuity': round(risky_annuity, 6),
    }


def compute_basis_delta(gauge_hazard_rate: float, basis_bps: float,
                        tenor: int, notional: float,
                        recovery: float = 0.0,
                        risk_free_rate: float = 0.03,
                        yield_curve: dict = None) -> Dict:
    """
    Compute basis delta for a property trade.

    When basis is approximately constant, the property spread tracks the
    gauge spread 1:1 through gauge rate changes, so basis delta ~ gauge delta.

    Args:
        gauge_hazard_rate: Gauge annual hazard rate
        basis_bps: Basis spread (gauge - property) in bps
        tenor: Remaining maturity in years
        notional: Trade notional
        recovery: Recovery rate
        risk_free_rate: Risk-free rate
        yield_curve: Optional yield curve for tenor-matched discounting

    Returns:
        Dict with basis_delta_bps, basis_dv01_gbp
    """
    gauge_spread_base = compute_prs_spread(
        gauge_hazard_rate, tenor, recovery, risk_free_rate,
        yield_curve=yield_curve)
    gauge_spread_bump = compute_prs_spread(
        gauge_hazard_rate + BUMP_1BP, tenor, recovery, risk_free_rate,
        yield_curve=yield_curve)

    delta_prop_spread = gauge_spread_bump - gauge_spread_base

    risky_annuity = compute_risky_annuity(
        gauge_hazard_rate, tenor, risk_free_rate, yield_curve)
    basis_dv01 = (delta_prop_spread / 10000) * risky_annuity * notional

    return {
        'basis_delta_bps': round(delta_prop_spread, 4),
        'basis_dv01_gbp': round(basis_dv01, 2),
    }


def compute_mark_to_market(trade_spread_bps: float,
                           fair_spread_bps: float,
                           risky_annuity: float,
                           notional: float,
                           is_payer: bool = True) -> float:
    """
    Mark-to-market of a PRS trade.

    MTM = (fair_spread - trade_spread) / 10000 * risky_annuity * notional * direction

    For a protection buyer (payer), positive MTM when fair spread > trade spread
    (market has moved in their favour — flood risk increased).

    Args:
        trade_spread_bps: Contracted spread at inception
        fair_spread_bps: Current fair market spread
        risky_annuity: Current risky annuity
        notional: Trade notional
        is_payer: True if protection buyer

    Returns:
        MTM value in GBP
    """
    direction = 1.0 if is_payer else -1.0
    spread_diff = (fair_spread_bps - trade_spread_bps) / 10000
    return round(spread_diff * risky_annuity * notional * direction, 2)
