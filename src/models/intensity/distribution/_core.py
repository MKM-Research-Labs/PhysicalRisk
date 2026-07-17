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
Storm intensity distribution with controllable tail behaviour.

Hybrid distribution:
- Below threshold: truncated normal distribution (historical behaviour)
- Above threshold: Pareto tail (controllable fat tail for stress scenarios)
"""

import random
from typing import Any, Dict, List, Optional

from ..parameters import SCENARIO_FAMILIES, DistributionParameters
from ._math import _MathMixin


class IntensityDistribution(_MathMixin):
    """
    Storm intensity distribution with controllable tail behaviour.

    Hybrid distribution:
    - Below tail_threshold: truncated normal
    - Above tail_threshold: Pareto tail

    The transition is smooth - the Pareto scale is calibrated so the
    PDF is continuous at the threshold.
    """

    def __init__(
        self,
        params: Optional[DistributionParameters] = None,
        base_mean: float = 45.0,
        base_std: float = 15.0,
        tail_threshold: float = 60.0,
        tail_index: float = 2.5,
        min_intensity: float = 10.0,
        max_intensity: float = 100.0,
        name: str = "custom",
        seed: Optional[int] = None
    ):
        """
        Initialize the distribution.

        Can pass either a DistributionParameters object or individual parameters.
        """
        if params is not None:
            self.params = params
        else:
            self.params = DistributionParameters(
                base_mean=base_mean,
                base_std=base_std,
                tail_threshold=tail_threshold,
                tail_index=tail_index,
                min_intensity=min_intensity,
                max_intensity=max_intensity,
                name=name
            )

        if seed is not None:
            random.seed(seed)

        # Pre-compute the probability of being in the tail region
        # under the base normal distribution
        self._tail_prob = self._normal_exceedance(self.params.tail_threshold)

    @classmethod
    def from_scenario(cls, scenario_name: str, seed: Optional[int] = None) -> "IntensityDistribution":
        """Create distribution from a named scenario family."""
        if scenario_name not in SCENARIO_FAMILIES:
            available = ", ".join(SCENARIO_FAMILIES.keys())
            raise ValueError(f"Unknown scenario '{scenario_name}'. Available: {available}")
        return cls(params=SCENARIO_FAMILIES[scenario_name], seed=seed)

    def exceedance_probability(self, intensity: float) -> float:
        """
        Calculate probability of exceeding a given intensity.

        Args:
            intensity: Storm intensity level (0-100)

        Returns:
            Probability of exceeding this intensity
        """
        if intensity <= self.params.min_intensity:
            return 1.0
        if intensity >= self.params.max_intensity:
            return 0.0

        if intensity <= self.params.tail_threshold:
            return self._normal_exceedance(intensity)
        else:
            pareto_exceed = self._pareto_exceedance(intensity)
            return self._tail_prob * pareto_exceed

    def inverse_exceedance(self, probability: float) -> float:
        """
        Calculate intensity for a given exceedance probability.

        Args:
            probability: Exceedance probability (0-1)

        Returns:
            Intensity level
        """
        if probability <= 0:
            return self.params.max_intensity
        if probability >= 1:
            return self.params.min_intensity

        if probability >= self._tail_prob:
            z = self._inverse_normal(1 - probability)
            intensity = self.params.base_mean + z * self.params.base_std
        else:
            ratio = self._tail_prob / probability
            intensity = self.params.tail_threshold * (ratio ** (1 / self.params.tail_index))

        return max(self.params.min_intensity, min(self.params.max_intensity, intensity))

    def sample(self, n: int = 1) -> List[float]:
        """
        Generate n random intensity samples from the distribution.

        Args:
            n: Number of samples

        Returns:
            List of intensity values
        """
        samples = []

        for _ in range(n):
            u = random.random()
            intensity = self.inverse_exceedance(u)
            intensity += random.gauss(0, 0.5)
            intensity = max(self.params.min_intensity, min(self.params.max_intensity, intensity))
            samples.append(intensity)

        return samples

    def sample_single(self) -> float:
        """Generate a single random intensity sample."""
        return self.sample(1)[0]

    def summary_statistics(self, n_samples: int = 10000) -> Dict[str, float]:
        """
        Calculate summary statistics via Monte Carlo.

        Args:
            n_samples: Number of samples for estimation

        Returns:
            Dictionary of statistics
        """
        samples = self.sample(n_samples)
        sorted_samples = sorted(samples)

        def percentile(p):
            idx = int(len(sorted_samples) * p / 100)
            return sorted_samples[min(idx, len(sorted_samples) - 1)]

        return {
            "mean": sum(samples) / len(samples),
            "std": (sum((x - sum(samples)/len(samples))**2 for x in samples) / len(samples)) ** 0.5,
            "min": min(samples),
            "max": max(samples),
            "p10": percentile(10),
            "p25": percentile(25),
            "p50": percentile(50),
            "p75": percentile(75),
            "p90": percentile(90),
            "p95": percentile(95),
            "p99": percentile(99),
            "prob_exceed_60": sum(1 for x in samples if x > 60) / len(samples),
            "prob_exceed_70": sum(1 for x in samples if x > 70) / len(samples),
            "prob_exceed_80": sum(1 for x in samples if x > 80) / len(samples),
            "prob_exceed_90": sum(1 for x in samples if x > 90) / len(samples),
        }

    def return_period_intensity(self, return_period_years: float, storms_per_year: float = 20) -> float:
        """
        Calculate intensity for a given return period.

        Args:
            return_period_years: Return period in years (e.g., 100 for 1-in-100)
            storms_per_year: Average number of storms per year

        Returns:
            Intensity level for this return period
        """
        p = 1 / (return_period_years * storms_per_year)
        return self.inverse_exceedance(p)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize distribution to dictionary."""
        return {
            "parameters": self.params.to_dict(),
            "tail_probability": self._tail_prob
        }

    def describe(self) -> str:
        """Human-readable description of the distribution."""
        stats = self.summary_statistics(5000)
        return f"""
Intensity Distribution: {self.params.name}
{'=' * 50}
Parameters:
  Base mean:        {self.params.base_mean:.1f}
  Base std:         {self.params.base_std:.1f}
  Tail threshold:   {self.params.tail_threshold:.1f}
  Tail index:       {self.params.tail_index:.2f} ({'fat' if self.params.tail_index < 2 else 'moderate' if self.params.tail_index < 3 else 'thin'} tail)
  Range:            [{self.params.min_intensity:.0f}, {self.params.max_intensity:.0f}]

Summary Statistics (from {5000} samples):
  Mean:             {stats['mean']:.1f}
  Std Dev:          {stats['std']:.1f}
  Median (p50):     {stats['p50']:.1f}
  p90:              {stats['p90']:.1f}
  p95:              {stats['p95']:.1f}
  p99:              {stats['p99']:.1f}

Exceedance Probabilities:
  P(intensity > 60): {stats['prob_exceed_60']*100:.1f}%
  P(intensity > 70): {stats['prob_exceed_70']*100:.1f}%
  P(intensity > 80): {stats['prob_exceed_80']*100:.1f}%
  P(intensity > 90): {stats['prob_exceed_90']*100:.1f}%

Return Period Intensities (assuming 20 storms/year):
  1-in-10 year:     {self.return_period_intensity(10):.1f}
  1-in-50 year:     {self.return_period_intensity(50):.1f}
  1-in-100 year:    {self.return_period_intensity(100):.1f}
"""
