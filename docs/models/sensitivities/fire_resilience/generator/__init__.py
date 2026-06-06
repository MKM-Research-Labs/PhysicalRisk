# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Fire-Resilience Credit Model (MKM-FIRE-001) sensitivity analysis.

Generates LaTeX sensitivity tables for
``docs/models/fire_resilience/sensitivity_tables.tex`` by running the *actual*
end-to-end fire model (``simulate_asset_fire``) against a fixed baseline
commercial asset and varying one input at a time.

Reported metrics (the resilience-credit currency the PRS pricer consumes):

  * Containment rate (%) --- ``n_contained / n_fires``, conditional on a fire.
  * Loss frequency (annual, %) --- ``(n_partial + n_total) / n_sim``,
    unconditional.
  * Fire spread (bps) --- the full-conflagration PRS leg priced as
    ``(n_point_of_no_return / n_sim) * 10000`` (frequency x 100% loss-given-
    event), i.e. the exact quantity rendered in the Commercial PRS Pricer.

Six sensitivities are produced:

  1. Suppression-systems resilience level (Not assessed .. Verified)
  2. Building height / NumberOfStoreys (crossing the 4-storey fire-service reach)
  3. Passive defence: compartmentation resilience level
  4. Property condition (drives ignition frequency)
  5. Commercial type (drives the base ignition rate and class prior)
  6. Two-way interaction: storeys x suppression level (the headline
     fire-truck-reach behaviour, reported as fire spread in bps)

All values are produced from engineering-judgement seed parameters in
``config/fire_matrices.json`` and are therefore directional, not calibrated.
"""

from dataclasses import replace

import numpy as np

from config.fire import FireRunConfig, load_fire_config
from docs.models.sensitivities import latex_table, write_tables
from models.fire.containment import simulate_asset_fire
from models.fire.data_structures import AssetFireFeatures

# A large draw count keeps the conditional containment rate stable (the
# baseline ignites only ~2-4% of draws, so we need many draws to accumulate
# a few hundred fires per cell).
_N_SIM = 20000
_SEED = 20260606

_LEVELS = ["Not assessed", "Partial", "Meets minimum", "Enhanced", "Verified"]


def _baseline() -> AssetFireFeatures:
    """A mid-rise office at the reference 'Meets minimum' resilience.

    Three storeys keeps the baseline *below* the 4-storey fire-service reach,
    so the height sweep can show the reach cut-off cleanly.
    """
    return AssetFireFeatures(
        asset_id="C-SENS-BASE",
        commercial_type="Office",
        occupancy_status="Fully occupied",
        business_rates_category=None,
        property_condition="Fair",
        automatic_detection_level="Meets minimum",
        suppression_systems_level="Meets minimum",
        emergency_procedures_level="Meets minimum",
        structural_fire_resistance_level="Meets minimum",
        compartments_level="Meets minimum",
        fire_stopping_level="Meets minimum",
        external_materials_level="Meets minimum",
        access_route_level="Meets minimum",
        business_continuity_level="Meets minimum",
        fire_damage_severity=None,
        years_since_last_fire=None,
        number_of_storeys=3,
    )


def _metrics(features: AssetFireFeatures, seed: int = _SEED):
    """Run the model once and return (containment %, loss-freq %, spread bps)."""
    cfg = load_fire_config(run=FireRunConfig(n_sim=_N_SIM))
    rng = np.random.default_rng(seed)
    r = simulate_asset_fire(features, cfg, rng)
    containment_pct = 100.0 * r.containment_rate
    loss_pct = 100.0 * r.loss_frequency
    spread_bps = 10000.0 * (r.n_point_of_no_return / r.n_sim if r.n_sim else 0.0)
    return containment_pct, loss_pct, spread_bps


def _sweep(field: str, values, label_fmt=str):
    """Vary one feature field across *values*; return rows of metrics."""
    base = _baseline()
    rows = []
    for v in values:
        feat = replace(base, **{field: v})
        cont, loss, bps = _metrics(feat)
        rows.append((label_fmt(v), cont, loss, bps))
    return rows


_HEADERS = ["", "Containment (\\%)", "Loss freq (\\%)", "Fire spread (bps)"]


def generate():
    """Build the six sensitivity tables for MKM-FIRE-001."""
    sections = []

    # 1. Suppression systems level.
    rows = _sweep("suppression_systems_level", _LEVELS)
    rows = [(("Suppression: " + r[0]),) + r[1:] for r in rows]
    sections.append(latex_table(
        caption="Fire-resilience credit by suppression-systems level "
                "(3-storey office baseline)",
        label="fire_suppression_sensitivity",
        headers=_HEADERS, rows=rows, col_fmt="lrrr"))

    # 2. Building height (storeys) --- crosses the 4-storey fire-service reach.
    rows = _sweep("number_of_storeys", [1, 3, 4, 5, 8, 12, 20],
                  label_fmt=lambda n: f"{n} storeys")
    sections.append(latex_table(
        caption="Fire-resilience credit by building height "
                "(reach = 4 storeys; 'Meets minimum' suppression)",
        label="fire_height_sensitivity",
        headers=_HEADERS, rows=rows, col_fmt="lrrr"))

    # 3. Passive defence: compartmentation level.
    rows = _sweep("compartments_level", _LEVELS)
    rows = [(("Compartments: " + r[0]),) + r[1:] for r in rows]
    sections.append(latex_table(
        caption="Fire-resilience credit by compartmentation level",
        label="fire_compartment_sensitivity",
        headers=_HEADERS, rows=rows, col_fmt="lrrr"))

    # 4. Property condition (ignition-frequency driver).
    rows = _sweep("property_condition",
                  ["Excellent", "Good", "Fair", "Poor", "Very poor"])
    sections.append(latex_table(
        caption="Fire-resilience credit by property condition",
        label="fire_condition_sensitivity",
        headers=_HEADERS, rows=rows, col_fmt="lrrr"))

    # 5. Commercial type (base ignition rate + class prior).
    rows = _sweep("commercial_type",
                  ["Office", "Retail", "Hotel", "Leisure", "Healthcare",
                   "MultiFamily", "MixedUse", "Other"])
    sections.append(latex_table(
        caption="Fire-resilience credit by commercial type",
        label="fire_type_sensitivity",
        headers=_HEADERS, rows=rows, col_fmt="lrrr"))

    # 6. Two-way: storeys x suppression level (fire spread in bps).
    storeys = [3, 5, 8, 20]
    sup_levels = ["Partial", "Meets minimum", "Enhanced", "Verified"]
    base = _baseline()
    grid_rows = []
    for n in storeys:
        cells = [f"{n} storeys"]
        for lv in sup_levels:
            feat = replace(base, number_of_storeys=n,
                           suppression_systems_level=lv)
            _, _, bps = _metrics(feat)
            cells.append(bps)
        grid_rows.append(tuple(cells))
    grid_headers = [""] + [f"{lv}" for lv in sup_levels]
    sections.append(latex_table(
        caption="Fire spread (bps) by height $\\times$ suppression level "
                "--- the fire-service-reach interaction",
        label="fire_height_suppression_grid",
        headers=grid_headers, rows=grid_rows,
        col_fmt="l" + "r" * len(sup_levels)))

    content = (
        "% Baseline: fully-occupied 3-storey Office, Fair condition, all "
        "resilience fields at 'Meets minimum'; one input varied at a time; "
        f"{_N_SIM:,} Monte Carlo draws per cell (seed {_SEED}).\n"
        "% Fire spread (bps) = (n\\_point\\_of\\_no\\_return / n\\_sim) * 10000 "
        "--- the full-conflagration PRS leg.\n\n".replace(",", "{,}")
        + "\n\n".join(sections)
    )
    write_tables("fire_resilience", content)


if __name__ == "__main__":
    generate()
