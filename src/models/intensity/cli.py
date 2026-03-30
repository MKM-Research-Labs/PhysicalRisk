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
CLI and comparison utilities for the intensity distribution model.
"""

import json
from typing import List

from .distribution import IntensityDistribution
from .parameters import SCENARIO_FAMILIES


def compare_scenarios(scenario_names: List[str] = None) -> str:
    """Compare multiple scenario families."""
    if scenario_names is None:
        scenario_names = list(SCENARIO_FAMILIES.keys())

    output = ["Scenario Comparison", "=" * 80]
    output.append(f"{'Scenario':<20} {'Mean':>8} {'P90':>8} {'P99':>8} {'P(>70)':>10} {'P(>80)':>10} {'1-in-100':>10}")
    output.append("-" * 80)

    for name in scenario_names:
        dist = IntensityDistribution.from_scenario(name)
        stats = dist.summary_statistics(5000)
        rp100 = dist.return_period_intensity(100)
        output.append(
            f"{name:<20} {stats['mean']:>8.1f} {stats['p90']:>8.1f} {stats['p99']:>8.1f} "
            f"{stats['prob_exceed_70']*100:>9.1f}% {stats['prob_exceed_80']*100:>9.1f}% {rp100:>10.1f}"
        )

    return "\n".join(output)


def main():
    """Command-line interface for intensity distribution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Storm Intensity Distribution Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show baseline distribution
  python -m models.intensity

  # Compare all scenarios
  python -m models.intensity --compare

  # Generate samples with custom parameters
  python -m models.intensity --samples 100 --tail-index 1.5

  # Use named scenario
  python -m models.intensity --scenario severe_stress

  # Calculate return period intensity
  python -m models.intensity --return-period 100
"""
    )

    parser.add_argument("--scenario", "-s", type=str, default=None,
                        help=f"Named scenario: {', '.join(SCENARIO_FAMILIES.keys())}")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Compare all scenario families")
    parser.add_argument("--samples", "-n", type=int, default=0,
                        help="Generate n samples and print them")
    parser.add_argument("--base-mean", type=float, default=45.0,
                        help="Base distribution mean (default: 45)")
    parser.add_argument("--base-std", type=float, default=15.0,
                        help="Base distribution std (default: 15)")
    parser.add_argument("--tail-threshold", type=float, default=60.0,
                        help="Threshold where Pareto tail begins (default: 60)")
    parser.add_argument("--tail-index", "-t", type=float, default=2.5,
                        help="Pareto tail index, lower=fatter (default: 2.5)")
    parser.add_argument("--return-period", "-r", type=float, default=None,
                        help="Calculate intensity for this return period (years)")
    parser.add_argument("--exceedance", "-e", type=float, default=None,
                        help="Calculate probability of exceeding this intensity")
    parser.add_argument("--json", action="store_true",
                        help="Output in JSON format")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")

    args = parser.parse_args()

    if args.compare:
        print(compare_scenarios())
        return

    if args.scenario:
        dist = IntensityDistribution.from_scenario(args.scenario, seed=args.seed)
    else:
        dist = IntensityDistribution(
            base_mean=args.base_mean,
            base_std=args.base_std,
            tail_threshold=args.tail_threshold,
            tail_index=args.tail_index,
            seed=args.seed
        )

    if args.return_period:
        intensity = dist.return_period_intensity(args.return_period)
        if args.json:
            print(json.dumps({"return_period_years": args.return_period, "intensity": intensity}))
        else:
            print(f"1-in-{args.return_period:.0f} year intensity: {intensity:.1f}")
        return

    if args.exceedance:
        prob = dist.exceedance_probability(args.exceedance)
        if args.json:
            print(json.dumps({"intensity": args.exceedance, "exceedance_probability": prob}))
        else:
            print(f"P(intensity > {args.exceedance:.0f}) = {prob*100:.2f}%")
        return

    if args.samples > 0:
        samples = dist.sample(args.samples)
        if args.json:
            print(json.dumps({"samples": samples, "parameters": dist.params.to_dict()}))
        else:
            print(f"Generated {args.samples} samples:")
            for i, s in enumerate(samples):
                print(f"  {i+1}: {s:.1f}")
        return

    if args.json:
        output = dist.to_dict()
        output["summary_statistics"] = dist.summary_statistics()
        print(json.dumps(output, indent=2))
    else:
        print(dist.describe())
