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

"""Loss structures for the Event Frequency Model (MKM-EF-001), Stage 6.

The occurrence model asks of each event only whether it floods a subject. Give
each event a *loss quantum* instead of a boolean and the same year sampler
becomes a year-loss table: the losses of the events drawn into a simulated year
sum to that year's aggregate loss, and their maximum is that year's largest
single occurrence. Repeating gives the two distributions the catastrophe desk
reasons in.

- **AEP** (aggregate exceedance probability) reads off the annual *aggregate*
  loss — what a stop-loss or an aggregate cover attaches to.
- **OEP** (occurrence exceedance probability) reads off the annual *largest
  single event* — what a per-occurrence excess-of-loss cover attaches to.

The **event loss table** (ELT) is the same information in the reinsurance
market's standard shape: one row per catalogue event carrying its annual rate
and its loss to the subject. Its average annual loss, ``sum(rate * loss)``, is
the simulation's exact expectation, which is what makes it a reconciliation
target rather than a second opinion (see ``ylt/_reconcile.py``).
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass(frozen=True)
class LossSimulation:
    """The annual loss distribution from a Monte Carlo run for one subject.

    Losses are assumed non-negative — they are damage quanta — which is what
    lets a year with no events carry a maximum occurrence loss of zero rather
    than of negative infinity.

    Attributes:
        n_years: number of years simulated.
        lambda_per_year: the catchment arrival rate used (over all qualifying
            events, before the catalogue-coverage scaling the sampler applies).
        aggregate_loss_per_year: total loss in each simulated year — the sum of
            the losses of every event drawn into that year.
        max_event_loss_per_year: the largest single-event loss in each simulated
            year; zero for a year in which no event arrived.
        seed: the seed the run used, so it reproduces exactly.
    """

    n_years: int
    lambda_per_year: float
    aggregate_loss_per_year: np.ndarray
    max_event_loss_per_year: np.ndarray
    seed: int

    def average_annual_loss(self) -> float:
        """Return the mean aggregate annual loss (AAL).

        The single number a premium is built from. It is the simulation's
        estimate of ``lambda_effective * E[loss per event]``, which the ELT
        reports in closed form.

        Returns:
            Expected loss per year; zero for an empty run.
        """
        if self.n_years == 0:
            return 0.0
        return float(self.aggregate_loss_per_year.mean())

    def aggregate_exceedance_probability(self, threshold: float) -> float:
        """Return the AEP at a loss level — P(annual aggregate loss > level).

        Args:
            threshold: the aggregate-loss level to exceed.

        Returns:
            A probability in ``[0, 1]``; zero for an empty run.
        """
        if self.n_years == 0:
            return 0.0
        return float(np.count_nonzero(self.aggregate_loss_per_year > threshold)
                     / self.n_years)

    def occurrence_exceedance_probability(self, threshold: float) -> float:
        """Return the OEP at a loss level — P(largest single event > level).

        Args:
            threshold: the single-occurrence loss level to exceed.

        Returns:
            A probability in ``[0, 1]``; zero for an empty run.
        """
        if self.n_years == 0:
            return 0.0
        return float(np.count_nonzero(self.max_event_loss_per_year > threshold)
                     / self.n_years)

    def aep_curve(self, return_periods: Tuple[int, ...]) -> Dict[int, float]:
        """Return the aggregate loss reached at each return period.

        The loss at return period ``T`` is the ``1 - 1/T`` quantile of the
        annual aggregate-loss distribution — the level exceeded once every
        ``T`` years on average.

        Args:
            return_periods: return periods in years.

        Returns:
            Mapping of return period to aggregate loss. An empty run maps every
            period to zero.
        """
        return self._curve(self.aggregate_loss_per_year, return_periods)

    def oep_curve(self, return_periods: Tuple[int, ...]) -> Dict[int, float]:
        """Return the single-occurrence loss reached at each return period.

        As ``aep_curve`` but over the annual *maximum* single-event loss.

        Args:
            return_periods: return periods in years.

        Returns:
            Mapping of return period to occurrence loss.
        """
        return self._curve(self.max_event_loss_per_year, return_periods)

    def _curve(
        self, losses: np.ndarray, return_periods: Tuple[int, ...]
    ) -> Dict[int, float]:
        """Return the loss at each return period from a per-year loss series."""
        if self.n_years == 0:
            return {rp: 0.0 for rp in return_periods}
        return {
            rp: float(np.quantile(losses, 1.0 - 1.0 / rp))
            for rp in return_periods
        }


@dataclass(frozen=True)
class EventLossTable:
    """One row per catalogue event: its annual rate and its loss to a subject.

    This is the reinsurance market's standard event-loss-table shape, which is
    what makes the model's output comparable with a third-party catastrophe
    model. Each event's rate is ``lambda_effective * weight``: the arrival rate
    of catalogue-representable events times the event's share of the sampling
    distribution, so the rates sum to ``lambda_effective``.

    The loss per event is a point estimate — the subject's loss for that event
    is determined once the event is drawn — so the usual independent and
    correlated standard-deviation columns are zero here.

    Attributes:
        subject_id: the gauge, property or portfolio the losses are for.
        event_ids: the catalogue events, aligned with ``rates`` and ``losses``.
        rates: annual occurrence rate of each event, in events per year.
        losses: the loss each event causes the subject.
        lambda_effective: the arrival rate of catalogue-representable events,
            ``lambda_per_year * coverage``; the rates sum to it.
    """

    subject_id: str
    event_ids: Tuple[str, ...]
    rates: np.ndarray
    losses: np.ndarray
    lambda_effective: float

    @property
    def n_events(self) -> int:
        """Return the number of events in the table."""
        return len(self.event_ids)

    def average_annual_loss(self) -> float:
        """Return the closed-form AAL, ``sum(rate * loss)``.

        This is the exact expectation of the year simulation's mean aggregate
        loss, not an alternative estimate of it, so a gap between the two beyond
        sampling error means one of them is wrong.

        Returns:
            Expected loss per year; zero for an empty table.
        """
        if self.n_events == 0:
            return 0.0
        return float(np.dot(self.rates, self.losses))

    def rows(self) -> List[dict]:
        """Return the table as standard event-loss-table rows.

        The column names follow the common catastrophe-model export so the
        table drops into a third-party comparison without translation.

        Returns:
            One dict per event with ``EventID``, ``Rate``, ``MeanLoss``,
            ``StdDevIndependent``, ``StdDevCorrelated`` and ``ExposureValue``.
        """
        return [
            {
                "EventID": event_id,
                "Rate": float(rate),
                "MeanLoss": float(loss),
                "StdDevIndependent": 0.0,
                "StdDevCorrelated": 0.0,
                "ExposureValue": float(loss),
            }
            for event_id, rate, loss in zip(self.event_ids, self.rates, self.losses)
        ]
