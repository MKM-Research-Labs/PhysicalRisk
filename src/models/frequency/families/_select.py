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

"""Distribution-family selection (MKM-EF-001, Stage 2).

Choose Poisson or Negative Binomial per gauge, and — the part that matters —
be honest when neither is right.

The rule is not the naive "dispersion index above one, use NegBin". With fifty
annual counts a genuine Poisson process produces index values up to about 1.4
by chance alone, so the naive rule over-selects NegBin badly. Selection here
gates on a **chi-square dispersion test**: NegBin is chosen only when the counts
are over-dispersed at the configured significance *and* NegBin's AIC beats
Poisson's by a margin (NegBin nests Poisson, so a negligible AIC gain is not
evidence for the extra parameter).

Under-dispersion is recorded and flagged, never fitted. In this platform it is
largely an artefact of declustering rather than a physical regularity, and no
standard count distribution on the Poisson–NegBin axis can represent it: Poisson
is selected as the nearest fittable family and the flag says so.
"""

from dataclasses import dataclass
from typing import Optional, Sequence

from scipy import stats

from config.frequency import SelectionConfig

from ._negbin import NegBinFit, fit_negbin
from ._poisson import PoissonFit, fit_poisson

# Dispersion regimes recorded on a selection.
UNDER_DISPERSED = "under-dispersed"
POISSON_CONSISTENT = "poisson-consistent"
OVER_DISPERSED = "over-dispersed"


@dataclass(frozen=True)
class DispersionTest:
    """The chi-square dispersion test result.

    For a genuine Poisson process, ``(n - 1) * D`` is chi-square with ``n - 1``
    degrees of freedom, where ``D`` is the sample dispersion index. The two
    tail probabilities say whether the counts are more regular (under) or more
    clustered (over) than Poisson would produce by chance.

    Attributes:
        dispersion_index: sample variance over sample mean.
        statistic: ``(n - 1) * dispersion_index``.
        degrees_of_freedom: ``n - 1``.
        p_over: probability a Poisson process exceeds this statistic — small
            means significant over-dispersion.
        p_under: probability a Poisson process falls below it — small means
            significant under-dispersion.
        regime: which of the three regimes the counts fall in, at the
            configured significance.
    """

    dispersion_index: float
    statistic: float
    degrees_of_freedom: int
    p_over: float
    p_under: float
    regime: str


@dataclass(frozen=True)
class FamilySelection:
    """The outcome of selecting a family for one gauge.

    Attributes:
        family: the chosen family name.
        poisson: the Poisson fit (always computed).
        negbin: the Negative Binomial fit, or ``None`` when not fitted.
        dispersion: the dispersion test.
        forced: True when a configuration override chose the family.
        note: human-readable justification, recorded for effective challenge
            (SR 11-7) — the override reason, or why the data-driven rule landed
            where it did.
    """

    family: str
    poisson: PoissonFit
    negbin: Optional[NegBinFit]
    dispersion: DispersionTest
    forced: bool
    note: str

    @property
    def fit(self):
        """Return the fit object for the chosen family."""
        if self.family == "negbin" and self.negbin is not None:
            return self.negbin
        return self.poisson


def dispersion_test(counts: Sequence[int], significance: float) -> DispersionTest:
    """Run the chi-square dispersion test on an annual count series.

    Args:
        counts: annual event counts.
        significance: two-sided level for classifying the regime.

    Returns:
        A ``DispersionTest``. A series shorter than two years, or with a zero
        mean, has no testable dispersion and is reported Poisson-consistent
        with unit p-values.
    """
    n = len(counts)
    mean = sum(counts) / n if n else 0.0
    if n < 2 or mean <= 0:
        return DispersionTest(
            dispersion_index=0.0,
            statistic=0.0,
            degrees_of_freedom=max(0, n - 1),
            p_over=1.0,
            p_under=1.0,
            regime=POISSON_CONSISTENT,
        )

    variance = sum((c - mean) ** 2 for c in counts) / (n - 1)
    index = variance / mean
    dof = n - 1
    statistic = dof * index
    p_over = float(stats.chi2.sf(statistic, dof))
    p_under = float(stats.chi2.cdf(statistic, dof))

    half = significance / 2.0
    if p_over < half:
        regime = OVER_DISPERSED
    elif p_under < half:
        regime = UNDER_DISPERSED
    else:
        regime = POISSON_CONSISTENT

    return DispersionTest(
        dispersion_index=index,
        statistic=statistic,
        degrees_of_freedom=dof,
        p_over=p_over,
        p_under=p_under,
        regime=regime,
    )


def select_family(
    counts: Sequence[int],
    config: SelectionConfig,
) -> FamilySelection:
    """Select a distribution family for an annual count series.

    Args:
        counts: annual event counts; must be non-empty.
        config: selection knobs, including any forced family.

    Returns:
        A ``FamilySelection`` carrying both fits, the dispersion test, and the
        justification for the choice.
    """
    poisson = fit_poisson(counts)
    test = dispersion_test(counts, config.overdispersion_significance)

    if config.force_family is not None:
        family = str(config.force_family)
        negbin = fit_negbin(counts) if family == "negbin" else None
        return FamilySelection(
            family=family,
            poisson=poisson,
            negbin=negbin,
            dispersion=test,
            forced=True,
            note=f"family forced to '{family}' by configuration override",
        )

    if test.regime == UNDER_DISPERSED:
        return FamilySelection(
            family="poisson",
            poisson=poisson,
            negbin=None,
            dispersion=test,
            forced=False,
            note=(
                "counts are significantly under-dispersed "
                f"(index {test.dispersion_index:.2f}, p={test.p_under:.3f}); no "
                "count family on the Poisson-NegBin axis represents this, so "
                "Poisson is selected as the nearest fittable family and the "
                "regime is flagged. In this platform under-dispersion is "
                "largely a declustering artefact."
            ),
        )

    if test.regime != OVER_DISPERSED:
        return FamilySelection(
            family="poisson",
            poisson=poisson,
            negbin=None,
            dispersion=test,
            forced=False,
            note=(
                f"counts consistent with Poisson (index {test.dispersion_index:.2f}, "
                f"p_over={test.p_over:.3f}); the simpler family is kept"
            ),
        )

    # Over-dispersed: fit NegBin and keep it only if AIC clearly prefers it.
    negbin = fit_negbin(counts)
    aic_gain = poisson.aic - negbin.aic
    if aic_gain >= config.prefer_poisson_within_aic:
        return FamilySelection(
            family="negbin",
            poisson=poisson,
            negbin=negbin,
            dispersion=test,
            forced=False,
            note=(
                "counts significantly over-dispersed "
                f"(index {test.dispersion_index:.2f}, p={test.p_over:.3f}); "
                f"NegBin AIC lower by {aic_gain:.1f}"
            ),
        )

    return FamilySelection(
        family="poisson",
        poisson=poisson,
        negbin=negbin,
        dispersion=test,
        forced=False,
        note=(
            "counts over-dispersed but NegBin AIC gain "
            f"{aic_gain:.1f} is within the {config.prefer_poisson_within_aic} "
            "margin; Poisson kept as the parsimonious choice"
        ),
    )


def selection_to_dict(selection: FamilySelection) -> dict:
    """Serialise a family selection for the persisted rate document.

    Records the chosen family, both fits' parameters, the dispersion test, and
    the justification — everything an auditor needs to see why this gauge got
    the family it did (SR 11-7).

    Args:
        selection: the selection to serialise.

    Returns:
        A JSON-serialisable dictionary.
    """
    nb = selection.negbin
    return {
        "family": selection.family,
        "forced": selection.forced,
        "note": selection.note,
        "dispersion": {
            "index": selection.dispersion.dispersion_index,
            "regime": selection.dispersion.regime,
            "p_over": selection.dispersion.p_over,
            "p_under": selection.dispersion.p_under,
        },
        "poisson": {
            "lambda": selection.poisson.lam,
            "aic": selection.poisson.aic,
        },
        "negbin": None if nb is None else {
            "mu": nb.mu,
            "alpha": nb.alpha,
            "variance": nb.variance,
            "aic": nb.aic,
        },
    }
