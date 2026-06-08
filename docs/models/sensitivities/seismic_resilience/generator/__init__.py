# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Seismic-Resilience Credit Model (MKM-SEIS-001) sensitivity analysis.

Generates the Section 7 LaTeX tables for
``docs/models/seismic_resilience/sensitivity_tables.tex`` by running the *actual*
end-to-end seismic model (``simulate_asset_seismic``) against the Section 7.1
baseline and varying one axis at a time over 20,000 Monte Carlo draws per cell.

Eight tables cover the three primary axes and the two headline interactions:

  1. Distance (R_JB)                      2. Distance x construction
  3. Intensity (hazard zone)              4. Zone x soil (soft-soil F_a gate)
  5. Resilience (BRI level)               6. Individual BRI measures
  7. Intensity x resilience               8. Distance x resilience

It then evaluates the Section 7.7 acceptance gates (distance / intensity /
resilience monotonicity, the interaction ordering, and the near-zero floor) and
prints PASS/FAIL for each. All values are produced from engineering-judgement
seed parameters and are therefore directional, not calibrated.
"""

from docs.models.sensitivities import latex_table, write_tables
from docs.models.sensitivities.seismic_resilience.generator._support import (
    BRI, CONSTRUCTION, HAZARD_CLASS, N_SIM, SEED, VS30, ZONES,
    baseline, metrics, replace,
)

# Spreads are coarse Monte-Carlo estimates (1 bps ~ 2 collapses in 20,000
# draws), so the monotonicity gates allow a small tolerance for sampling noise.
_TOL_BPS = 0.7


def _nonincreasing(xs):
    return all(xs[i + 1] <= xs[i] + _TOL_BPS for i in range(len(xs) - 1))


def _nondecreasing(xs):
    return all(xs[i + 1] >= xs[i] - _TOL_BPS for i in range(len(xs) - 1))


def _spread_grid(row_labels, row_features):
    """Build (rows, grid_of_spreads) for an interaction table — one spread per
    cell. ``row_features`` maps a row label to a list of per-column features."""
    rows, grid = [], []
    for label in row_labels:
        spreads = [metrics(f)[3] for f in row_features[label]]
        rows.append((label, *spreads))
        grid.append(spreads)
    return rows, grid


def generate():
    """Build the eight Section 7 tables and evaluate the Section 7.7 gates."""
    sections = []
    gate = {}

    # --- Table 1: Distance (R_JB) -----------------------------------------
    distances = [2, 5, 10, 20, 50, 100]
    t1 = []
    for r in distances:
        pga, nc, loss, bps = metrics(baseline(r))
        t1.append((f"{r} km", pga, nc, loss, bps))
    gate["distance"] = [row[4] for row in t1]
    sections.append(latex_table(
        caption="Seismic credit by source-to-site distance $R_{JB}$ "
                "(RC pre-code, Moderate zone, all BRI absent)",
        label="seis_distance",
        headers=["$R_{JB}$", "Median PGA (g)", "No-collapse (\\%)",
                 "Loss freq (\\%)", "Spread (bps)"],
        rows=t1, col_fmt="lrrrr"))

    # --- Table 2: Distance x construction ---------------------------------
    c_labels = list(CONSTRUCTION)
    rows2, _ = _spread_grid(
        [f"{r} km" for r in [2, 10, 20, 50]],
        {f"{r} km": [replace(baseline(r), construction_type=CONSTRUCTION[c])
                     for c in c_labels] for r in [2, 10, 20, 50]})
    sections.append(latex_table(
        caption="Seismic spread (bps) by $R_{JB}$ $\\times$ construction type "
                "(Moderate zone, all BRI absent)",
        label="seis_distance_construction",
        headers=["$R_{JB}$", *c_labels], rows=rows2,
        col_fmt="l" + "r" * len(c_labels)))

    # --- Table 3: Intensity (hazard zone) ---------------------------------
    t3 = []
    for z in ZONES:
        feat = replace(baseline(), seismic_hazard_class=HAZARD_CLASS[z])
        pga, nc, loss, bps = metrics(feat)
        t3.append((z, nc, loss, bps))
    gate["intensity"] = [row[3] for row in t3]
    sections.append(latex_table(
        caption="Seismic credit by hazard zone "
                "(RC pre-code, $R_{JB}$ = 20 km, all BRI absent)",
        label="seis_intensity",
        headers=["Zone", "No-collapse (\\%)", "Loss freq (\\%)", "Spread (bps)"],
        rows=t3, col_fmt="lrrr"))

    # --- Table 4: Zone x soil (the soft-soil F_a gate) --------------------
    soil_cols = ["Rock (A)", "Stiff (B)", "Soft (D) no GS02", "Soft (D) GS02"]

    def _soil_feature(zone, col):
        f = replace(baseline(), seismic_hazard_class=HAZARD_CLASS[zone])
        if col == "Rock (A)":
            return replace(f, soil_vs30_mps=VS30["Rock (A)"])
        if col == "Stiff (B)":
            return replace(f, soil_vs30_mps=VS30["Stiff (B)"])
        if col == "Soft (D) no GS02":
            return replace(f, soil_vs30_mps=VS30["Soft (D)"])
        return replace(f, soil_vs30_mps=VS30["Soft (D)"], measures=frozenset({"GS02"}))

    soil_zones = ["Low", "Moderate", "High", "Very high"]
    rows4, _ = _spread_grid(
        soil_zones,
        {z: [_soil_feature(z, c) for c in soil_cols] for z in soil_zones})
    sections.append(latex_table(
        caption="Seismic spread (bps) by hazard zone $\\times$ soil type "
                "(RC pre-code, $R_{JB}$ = 20 km) --- the soft-soil amplification "
                "and GS02 gate",
        label="seis_zone_soil",
        headers=["Zone", *soil_cols], rows=rows4,
        col_fmt="l" + "r" * len(soil_cols)))

    # --- Table 5: Resilience (BRI level) ----------------------------------
    # Run near-fault (R_JB = 5 km) so the collapse leg is non-trivial and the
    # resilience differentiation is visible; at the 20 km baseline the Moderate
    # zone produces ~0 collapses for every BRI level (resilience credit is ~0
    # precisely where collapse is rare).
    _RES_RJB = 5.0
    t5 = []
    for pos in ["NR", "B", "A", "AA"]:
        feat = replace(baseline(_RES_RJB), measures=BRI[pos])
        pga, nc, loss, bps = metrics(feat)
        t5.append((pos, nc, loss, bps))
    gate["res_nocollapse"] = [row[1] for row in t5]
    gate["res_spread"] = [row[3] for row in t5]
    sections.append(latex_table(
        caption="Seismic credit by BRI resilience level "
                "(RC pre-code, Moderate zone, near-fault $R_{JB}$ = 5 km)",
        label="seis_resilience",
        headers=["BRI level", "No-collapse (\\%)", "Loss freq (\\%)",
                 "Spread (bps)"],
        rows=t5, col_fmt="lrrr"))

    # --- Table 6: Individual BRI measures ---------------------------------
    base_bps = metrics(baseline(_RES_RJB))[3]
    t6 = [("None (baseline)", metrics(baseline(_RES_RJB))[1], base_bps, 0.0)]
    for code, desc in [("GS08", "Lateral force resistance"),
                       ("GS09", "Connected / braced"),
                       ("GS12", "Base isolation"),
                       ("GS14", "No vertical irregularities"),
                       ("GS02", "Seismic foundation ($F_a$ gate)")]:
        feat = replace(baseline(_RES_RJB), measures=frozenset({code}))
        _, nc, _, bps = metrics(feat)
        t6.append((f"{code}: {desc}", nc, bps, bps - base_bps))
    sections.append(latex_table(
        caption="Seismic credit by individual BRI measure "
                "(single-measure sweeps; Moderate zone, near-fault "
                "$R_{JB}$ = 5 km, RC pre-code, stiff soil)",
        label="seis_individual_measures",
        headers=["Measure", "No-collapse (\\%)", "Spread (bps)",
                 "$\\Delta$ spread"],
        rows=t6, col_fmt="lrrr"))

    # --- Table 7: Intensity x resilience (the headline non-linearity) -----
    pos7 = ["NR", "B", "A", "AA"]
    rows7, grid7 = _spread_grid(
        ZONES,
        {z: [replace(baseline(), seismic_hazard_class=HAZARD_CLASS[z],
                     measures=BRI[p]) for p in pos7] for z in ZONES})
    gate["vh_nr"] = grid7[ZONES.index("Very high")][pos7.index("NR")]
    gate["high_aa"] = grid7[ZONES.index("High")][pos7.index("AA")]
    gate["mod_aa"] = grid7[ZONES.index("Moderate")][pos7.index("AA")]
    sections.append(latex_table(
        caption="Seismic spread (bps) by hazard zone $\\times$ BRI resilience "
                "level (RC pre-code, $R_{JB}$ = 20 km) --- strong measures are "
                "most valuable in high-hazard zones",
        label="seis_intensity_resilience",
        headers=["Zone", *pos7], rows=rows7, col_fmt="l" + "r" * len(pos7)))

    # --- Table 8: Distance x resilience -----------------------------------
    d8 = [2, 10, 20, 50]
    rows8, _ = _spread_grid(
        [f"{r} km" for r in d8],
        {f"{r} km": [replace(baseline(r), measures=BRI[p]) for p in pos7]
         for r in d8})
    sections.append(latex_table(
        caption="Seismic spread (bps) by $R_{JB}$ $\\times$ BRI resilience "
                "level (RC pre-code, Moderate zone)",
        label="seis_distance_resilience",
        headers=["$R_{JB}$", *pos7], rows=rows8, col_fmt="l" + "r" * len(pos7)))

    # --- Section 7.7 near-zero floor: Very low zone at R_JB = 100 km -------
    gate["floor"] = metrics(
        replace(baseline(100), seismic_hazard_class=HAZARD_CLASS["Very low"]))[3]

    # --- Evaluate the Section 7.7 acceptance gates ------------------------
    checks = [
        ("Distance monotonic (spread non-increasing in R_JB)",
         _nonincreasing(gate["distance"])),
        ("Intensity monotonic (spread non-decreasing in zone)",
         _nondecreasing(gate["intensity"])),
        ("Resilience: no-collapse non-decreasing NR->AA",
         _nondecreasing(gate["res_nocollapse"])),
        ("Resilience: spread non-increasing NR->AA",
         _nonincreasing(gate["res_spread"])),
        ("Interaction (VeryHigh,NR) > (High,AA) >= (Moderate,AA)",
         gate["vh_nr"] > gate["high_aa"] and gate["high_aa"] >= gate["mod_aa"] - _TOL_BPS),
        ("Near-zero floor (Very low, R_JB=100 km) < 1 bps",
         gate["floor"] < 1.0),
    ]
    print("  Section 7.7 acceptance gates:")
    for name, ok in checks:
        print(f"    [{'PASS' if ok else 'FAIL'}] {name}")
    gate_summary = "; ".join(
        f"{'PASS' if ok else 'FAIL'} {name}" for name, ok in checks)

    content = (
        "% Baseline (Section 7.1): 4-storey Office, Fair, RC pre-code, stiff "
        "soil (class B), Moderate zone, 20 km from the fault, all BRI absent; "
        f"one axis varied at a time; {N_SIM:,} draws per cell (seed {SEED}).\n"
        "% Seismic spread (bps) = (n_DS3 / n_sim) * 10000 --- the full-collapse "
        "PRS leg.\n"
        f"% Section 7.7 gates: {gate_summary}\n\n".replace(",", "{,}")
        + "\n\n".join(sections)
    )
    write_tables("seismic_resilience", content)


if __name__ == "__main__":
    generate()
