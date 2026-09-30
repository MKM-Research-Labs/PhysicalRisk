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

"""Flood hazard at the borrower's site, the losses it causes, and the PRS payout."""

from typing import Dict, Tuple

import numpy as np
from scipy.stats import genextreme

from config.capital import BorrowerConfig, CapitalReliefConfig, HazardConfig, PRSConfig


def simulate_drivers(cfg: CapitalReliefConfig) -> Dict[str, np.ndarray]:
    """Common random numbers shared by the with- and without-PRS runs.

    The draw order is part of the model: changing it changes every figure, and
    the recorded runs would no longer reproduce.
    """
    rng = np.random.default_rng(cfg.seed)
    h = cfg.hazard
    n = cfg.n_paths
    return {
        "z_ebitda": rng.standard_normal(n),
        # scipy's genextreme uses c = -xi
        "gauge_level": genextreme.rvs(
            c=-h.gev_shape_xi, loc=h.gev_loc, scale=h.gev_scale,
            size=n, random_state=rng,
        ),
        "depth_noise": rng.normal(0.0, h.depth_noise_sd, n),
    }


def flood_losses(gauge_level, depth_noise, b: BorrowerConfig,
                 h: HazardConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (site depth, uninsured remediation cost, business-interruption loss)."""
    depth = np.maximum(0.0, h.depth_slope * (gauge_level - h.site_flood_level)
                       + depth_noise)
    damage_frac = 1.0 - np.exp(-depth / h.damage_depth_scale)
    remediation = damage_frac * b.site_asset_value * (1.0 - b.insured_share_of_damage)
    downtime_months = h.max_downtime_months * damage_frac
    bi_loss = downtime_months / 12.0 * b.revenue * b.contribution_margin
    return depth, remediation, bi_loss


def prs_payout(gauge_level, p: PRSConfig) -> np.ndarray:
    """Parametric payout, linear between the attach and exhaust gauge levels."""
    frac = np.clip((gauge_level - p.attach_level) / (p.exhaust_level - p.attach_level),
                   0.0, 1.0)
    return p.notional * frac


def fixed_charges(b: BorrowerConfig) -> float:
    """Interest, amortisation and maintenance capex: paid every year, flood or not."""
    return b.debt * b.interest_rate + b.amortisation + b.maintenance_capex


def year_end_liquidity(drivers, b: BorrowerConfig, remediation, bi_loss,
                       payout, premium) -> np.ndarray:
    ebitda = b.ebitda * (1.0 + b.ebitda_vol * drivers["z_ebitda"])
    return (b.liquidity + ebitda - fixed_charges(b) - premium
            - remediation - bi_loss + payout)
