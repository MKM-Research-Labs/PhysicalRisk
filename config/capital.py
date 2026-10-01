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

"""
PRS capital-relief parameters (MKM-CR-001, proposed; Tier 1).

Every number the capital-relief model uses: the borrower, the flood hazard at
its site, the PRS it holds, the bank's capital assumptions, the rating master
scale, the Basel IRB corporate formula constants, and the renewal-market
assumptions for cover rolled over the loan term.

ILLUSTRATIVE. The values are the ones the study in ``docs/capital/`` was run
with: a plausible BB+ mid-cap borrower in a flood plain, not calibrated to
observed data. The master scale and the standardised risk weights must be
replaced with the bank's own scale and the applicable rules (UK: PRA Basel 3.1)
before any figure is used for a decision.

Figures are in GBP millions and years. The dataclasses are frozen and their
field names are part of the audit record: ``fingerprint()`` hashes them, and the
package reproduces the hashes of the recorded study runs.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Tuple

from config.loan import CREDIT_RATING_SPREADS

STATUS = "ILLUSTRATIVE - parameters not calibrated to observed data"

SEED = 20260930
ONE_YEAR_PATHS = 2_000_000
OVER_TERM_PATHS = 1_000_000


@dataclass(frozen=True)
class BorrowerConfig:
    revenue: float = 50.0
    ebitda: float = 8.0                    # 16% margin
    ebitda_vol: float = 0.32               # one-year EBITDA shock vol (non-hazard)
    debt: float = 32.0                     # 4.0x leverage, all bank debt
    interest_rate: float = 0.07
    amortisation: float = 2.0
    maintenance_capex: float = 1.5
    liquidity: float = 5.0                 # cash + undrawn RCF
    site_asset_value: float = 8.0          # flood-exposed plant, stock, fit-out
    contribution_margin: float = 0.40      # EBITDA lost per unit revenue lost
    insured_share_of_damage: float = 0.50  # commercial flood cover in high-hazard
                                           # zones is often restricted


@dataclass(frozen=True)
class HazardConfig:
    # Annual-maximum gauge level (m), GEV. xi > 0 is a heavy (Frechet) tail.
    gev_loc: float = 4.00
    gev_scale: float = 0.30
    gev_shape_xi: float = 0.10
    # The site floods above this gauge level; depth = slope * (L - level) + noise.
    site_flood_level: float = 5.55
    depth_slope: float = 1.00
    depth_noise_sd: float = 0.15           # gauge-to-site basis risk
    damage_depth_scale: float = 0.60       # damage fraction = 1 - exp(-depth / scale)
    max_downtime_months: float = 3.0       # downtime = max * damage fraction


@dataclass(frozen=True)
class PRSConfig:
    notional: float = 6.0
    attach_level: float = 5.50             # gauge level where payout starts
    exhaust_level: float = 6.05            # gauge level for the full notional
    premium_loading: float = 0.50          # premium = E[payout] * (1 + loading)


# The funding saving a borrower gets from an upgrade into investment grade.
# Derived from the loan pricer's own rating spreads (BB to BBB) rather than set
# here, so the two models cannot disagree about what a grade is worth.
IG_CREDIT_SPREAD_BENEFIT = CREDIT_RATING_SPREADS["BB"] - CREDIT_RATING_SPREADS["BBB"]


@dataclass(frozen=True)
class CapitalConfig:
    lgd: float = 0.45
    maturity_years: float = 2.5
    capital_ratio: float = 0.105           # 8% + 2.5% conservation buffer
    cost_of_equity: float = 0.12
    ig_credit_spread_benefit: float = IG_CREDIT_SPREAD_BENEFIT


@dataclass(frozen=True)
class CapitalReliefConfig:
    """One-year capital relief: a borrower, its hazard, its PRS, the bank."""
    borrower: BorrowerConfig = field(default_factory=BorrowerConfig)
    hazard: HazardConfig = field(default_factory=HazardConfig)
    prs: PRSConfig = field(default_factory=PRSConfig)
    capital: CapitalConfig = field(default_factory=CapitalConfig)
    n_paths: int = ONE_YEAR_PATHS
    seed: int = SEED

    def fingerprint(self) -> str:
        return _sha256(self)


@dataclass(frozen=True)
class OverTermConfig:
    """The same borrower over the loan term, under four cover modes.

    The field is named ``example`` because the study it reproduces named it so,
    and the name is part of the hashed audit record.
    """
    example: CapitalReliefConfig = field(
        default_factory=lambda: CapitalReliefConfig(n_paths=OVER_TERM_PATHS))
    tenor_years: int = 5
    gev_loc_drift_per_year: float = 0.01       # m/yr rise in the annual-max level
    post_payout_premium_uplift: float = 1.0    # rolled premium x (1 + uplift) after a payout
    withdrawal_prob_after_payout: float = 0.30  # market withdraws cover after a payout
    # A market-wide hard market (e.g. after a catastrophe elsewhere): rolled
    # cover reprices for everyone or capacity withdraws. Not borrower-specific.
    hard_market_prob_per_year: float = 0.10
    hard_market_premium_multiple: float = 3.0
    hard_market_withdrawal_prob: float = 0.25
    # Surplus cash above opening liquidity is distributed or reinvested.
    cap_liquidity_at_opening: bool = True

    def fingerprint(self) -> str:
        return _sha256(self)


def _sha256(cfg) -> str:
    return hashlib.sha256(json.dumps(asdict(cfg), sort_keys=True).encode()).hexdigest()


COVER_MODES: Tuple[str, ...] = ("none", "one_year_only", "annual_renewal", "embedded")

# Illustrative master scale: (grade, upper PD bound, SA corporate risk weight).
MASTER_SCALE: Tuple[Tuple[str, float, float], ...] = (
    ("A-",   0.0007, 0.50),
    ("BBB+", 0.0012, 0.75),
    ("BBB",  0.0020, 0.75),
    ("BBB-", 0.0035, 0.75),
    ("BB+",  0.0060, 1.00),
    ("BB",   0.0100, 1.00),
    ("BB-",  0.0170, 1.00),
    ("B+",   0.0300, 1.50),
    ("B",    1.0000, 1.50),
)

# Basel IRB corporate risk-weight function (no SME adjustment).
IRB_PD_FLOOR = 0.0005                  # Basel III corporate PD floor, 5bp
IRB_CORRELATION_MIN = 0.12
IRB_CORRELATION_MAX = 0.24
IRB_CORRELATION_DECAY = 50.0
IRB_MATURITY_A = 0.11852
IRB_MATURITY_B = 0.05478
IRB_MATURITY_REFERENCE = 2.5
IRB_MATURITY_SLOPE = 1.5
IRB_CONFIDENCE = 0.999
IRB_RW_MULTIPLIER = 12.5               # 1 / 8%


# ---------------------------------------------------------------------------
# A real commercial asset (WP2): the borrower is the property investor that owns
# it, and its flood hazard comes from the platform's event catalogue.
# ---------------------------------------------------------------------------

#: Which of the asset's nearest gauges the PRS references: the first real
#: (non-synthetic) one, as the property PRS book does. Depth is driven by the
#: controlling synthetic gauge, so the two can differ -- that is the basis risk.
SYNTHETIC_GAUGE_PREFIX = "SYNTH"

#: The flood series the depths are read from (the surveyed floor, not BRI).
ASSET_TIMESERIES_MODE = "flood"

#: Share of the balance each repayment type amortises over the remaining term,
#: keyed by the CDM's RepaymentType options. An unknown type is treated as
#: interest only, which understates debt service rather than inventing it.
AMORTISING_SHARE = {"Repayment": 1.0, "Part and part": 0.5, "Interest only": 0.0}


@dataclass(frozen=True)
class InvestorConfig:
    """What the commercial CDM does not carry about the investor who owns the asset.

    Income, debt and the building come from the asset and its loan; these fill
    the gaps. All illustrative until calibrated.
    """
    income_vol: float = 0.15               # one-year shock vol of net rent (voids, arrears)
    liquidity_months_of_debt_service: float = 6.0   # cash + undrawn facilities
    building_share_of_value: float = 0.60  # reinstatement share of market value (land excluded)
    insured_share_of_damage: float = 0.50  # as the study: flood cover is often restricted
    max_downtime_months: float = 3.0       # rent lost = rent x downtime, downtime = max x damage
    # The PRS notional is not a parameter: it is sized to the asset's uninsured
    # flood loss (see models.capital.asset_one_year.size_notional).


@dataclass(frozen=True)
class AssetRunConfig:
    """One-year capital relief for a real asset, on the platform's event years."""
    investor: InvestorConfig = field(default_factory=InvestorConfig)
    capital: CapitalConfig = field(default_factory=CapitalConfig)
    n_years: int = ONE_YEAR_PATHS
    seed: int = SEED

    def fingerprint(self) -> str:
        return _sha256(self)
