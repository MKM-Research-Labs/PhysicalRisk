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
Distribution parameters and pre-defined scenario families.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class DistributionParameters:
    """
    Parameters defining the intensity distribution.

    Attributes:
        base_mean: Mean of the base (normal) distribution
        base_std: Standard deviation of the base distribution
        tail_threshold: Intensity level where Pareto tail begins
        tail_index: Pareto tail index (alpha). Lower = fatter tail.
                   alpha=3.0 thin tail, alpha=1.0 very fat tail
        min_intensity: Minimum intensity (floor)
        max_intensity: Maximum intensity (cap)
        name: Human-readable name for this configuration
    """
    base_mean: float = 45.0
    base_std: float = 15.0
    tail_threshold: float = 60.0
    tail_index: float = 2.5
    min_intensity: float = 10.0
    max_intensity: float = 100.0
    name: str = "baseline"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DistributionParameters":
        return cls(**d)


# Pre-defined scenario families
SCENARIO_FAMILIES = {
    "historical": DistributionParameters(
        base_mean=40.0,
        base_std=12.0,
        tail_threshold=60.0,
        tail_index=3.0,
        name="historical"
    ),
    "baseline": DistributionParameters(
        base_mean=45.0,
        base_std=15.0,
        tail_threshold=60.0,
        tail_index=2.5,
        name="baseline"
    ),
    "moderate_stress": DistributionParameters(
        base_mean=50.0,
        base_std=15.0,
        tail_threshold=55.0,
        tail_index=2.0,
        name="moderate_stress"
    ),
    "severe_stress": DistributionParameters(
        base_mean=55.0,
        base_std=18.0,
        tail_threshold=50.0,
        tail_index=1.5,
        name="severe_stress"
    ),
    "extreme": DistributionParameters(
        base_mean=60.0,
        base_std=20.0,
        tail_threshold=45.0,
        tail_index=1.2,
        name="extreme"
    ),
}
