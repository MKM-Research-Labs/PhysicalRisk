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

"""BRI Resilience Model sensitivity analysis.

Generates LaTeX sensitivity tables for `docs/models/bri_resilience/sensitivity_tables.tex`.
Four sensitivities are reported, each holding a baseline property and varying one
dimension:

  1. Construction period (Pre-1919 .. 2009-Present)
  2. EA flood zone (Zone 1 .. Zone 3b)
  3. Property condition (Excellent .. Very poor)
  4. Flood regime (pluvial / fluvial / coastal)

Each table shows the mean flood resilience score (0-100) over a small sample with
matched seeds.
"""

import random
from statistics import mean

from docs.models.sensitivities import latex_table, write_tables


_SAMPLE_SIZE = 200


def _baseline_property():
    """A modern Thames property in Zone 2 with Meets-minimum compliance."""
    return {
        "PropertyHeader": {
            "Header": {"PropertyID": "P-SENS-BASE"},
            "PropertyAttributes": {
                "PropertyPeriod":    "1976-1999",
                "PropertyCondition": "Fair",
            },
            "Construction": {
                "FloorLevelMeters": 2.5,
                "BasementPresent": False,
            },
            "RiskAssessment": {
                "EAFloodZone":  "Zone 2",
                "FloodRiskType": "Fluvial",
            },
        },
    }


def _score_with_override(base, key_path, value, n=_SAMPLE_SIZE, seed=0):
    """Return mean flood score over n samples with one input overridden."""
    from copy import deepcopy
    from port.rand.thames.property.property_random.resilience import (
        generate_resilience, compute_flood_resilience_score,
    )

    scores = []
    for i in range(n):
        rng = random.Random(seed + i)
        prop = deepcopy(base)
        # Apply override at the given path.
        cur = prop
        for k in key_path[:-1]:
            cur = cur.setdefault(k, {})
        cur[key_path[-1]] = value
        # Generate resilience based on the (possibly overridden) inputs.
        prop["ProtectionMeasures"] = {"ResilienceMeasures": generate_resilience(prop, rng)}
        scores.append(compute_flood_resilience_score(prop)["score_final"])
    return mean(scores)


def generate():
    """Build sensitivity tables for the BRI Resilience Model."""
    base = _baseline_property()
    sections = []

    # 1. Period sensitivity
    period_rows = []
    for period in ("Pre-1919", "1919-1944", "1945-1975",
                   "1976-1999", "2000-2008", "2009-Present"):
        s = _score_with_override(
            base, ["PropertyHeader", "PropertyAttributes", "PropertyPeriod"], period
        )
        period_rows.append((period, s))
    sections.append(latex_table(
        caption="Mean flood resilience score by construction period",
        label="bri_period_sensitivity",
        headers=["Period", "Mean score (1-100)"],
        rows=period_rows,
        col_fmt="lr",
    ))

    # 2. Zone sensitivity
    zone_rows = []
    for zone in ("Zone 1", "Zone 2", "Zone 3a", "Zone 3b"):
        s = _score_with_override(
            base, ["PropertyHeader", "RiskAssessment", "EAFloodZone"], zone
        )
        zone_rows.append((zone, s))
    sections.append(latex_table(
        caption="Mean flood resilience score by EA flood zone",
        label="bri_zone_sensitivity",
        headers=["Zone", "Mean score (1-100)"],
        rows=zone_rows,
        col_fmt="lr",
    ))

    # 3. Condition sensitivity
    cond_rows = []
    for condition in ("Excellent", "Good", "Fair", "Poor", "Very poor"):
        s = _score_with_override(
            base, ["PropertyHeader", "PropertyAttributes", "PropertyCondition"], condition
        )
        cond_rows.append((condition, s))
    sections.append(latex_table(
        caption="Mean flood resilience score by property condition",
        label="bri_condition_sensitivity",
        headers=["Condition", "Mean score (1-100)"],
        rows=cond_rows,
        col_fmt="lr",
    ))

    # 4. Regime sensitivity (FloodRiskType change drives different regime weights).
    regime_rows = []
    for risk_type in ("Pluvial", "Fluvial", "Coastal"):
        s = _score_with_override(
            base, ["PropertyHeader", "RiskAssessment", "FloodRiskType"], risk_type
        )
        regime_rows.append((risk_type, s))
    sections.append(latex_table(
        caption="Mean flood resilience score by flood regime (FloodRiskType)",
        label="bri_regime_sensitivity",
        headers=["Regime", "Mean score (1-100)"],
        rows=regime_rows,
        col_fmt="lr",
    ))

    content = (
        "% Baseline: 1976-1999 Thames property in Zone 2 with Fair condition, "
        "Fluvial regime; one input varied at a time; "
        f"{_SAMPLE_SIZE} samples per row.\n\n"
        + "\n\n".join(sections)
    )
    write_tables("bri_resilience", content)


if __name__ == "__main__":
    generate()
