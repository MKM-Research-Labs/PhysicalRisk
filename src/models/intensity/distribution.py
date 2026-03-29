# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

import math
import random
from typing import Any, Dict, List, Optional

from .parameters import SCENARIO_FAMILIES, DistributionParameters


class IntensityDistribution:
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

    def _normal_pdf(self, x: float) -> float:
        """Standard normal PDF."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    def _normal_cdf(self, x: float) -> float:
        """Standard normal CDF using error function approximation."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _normal_exceedance(self, intensity: float) -> float:
        """Probability of exceeding intensity under base normal."""
        z = (intensity - self.params.base_mean) / self.params.base_std
        return 1 - self._normal_cdf(z)

    def _pareto_exceedance(self, intensity: float) -> float:
        """
        Probability of exceeding intensity under Pareto tail.

        P(X > x) = (x_m / x)^alpha for x >= x_m
        where x_m = tail_threshold
        """
        if intensity <= self.params.tail_threshold:
            return 1.0

        alpha = self.params.tail_index
        x_m = self.params.tail_threshold
        return (x_m / intensity) ** alpha

    def _inverse_normal(self, p: float) -> float:
        """Inverse normal CDF (quantile function). Rational approximation."""
        if p <= 0:
            return float('-inf')
        if p >= 1:
            return float('inf')

        a = [
            -3.969683028665376e+01,
            2.209460984245205e+02,
            -2.759285104469687e+02,
            1.383577518672690e+02,
            -3.066479806614716e+01,
            2.506628277459239e+00
        ]
        b = [
            -5.447609879822406e+01,
            1.615858368580409e+02,
            -1.556989798598866e+02,
            6.680131188771972e+01,
            -1.328068155288572e+01
        ]
        c = [
            -7.784894002430293e-03,
            -3.223964580411365e-01,
            -2.400758277161838e+00,
            -2.549732539343734e+00,
            4.374664141464968e+00,
            2.938163982698783e+00
        ]
        d = [
            7.784695709041462e-03,
            3.224671290700398e-01,
            2.445134137142996e+00,
            3.754408661907416e+00
        ]

        p_low = 0.02425
        p_high = 1 - p_low

        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                   ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5])*q / \
                   (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5]) / \
                    ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1)

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
