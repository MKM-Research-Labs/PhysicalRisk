# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Wind-coupled hazard-curve stages: win/faw/fow/bow/baw for property + commercial.

These scenarios sit alongside the flood spine (propertyhc) and the shd/she/bri
basis steps, following the IDENTICAL scenario protocol:

    flag  →  per-mode ts input dir  →  hc generator(mode)  →  hc output json

    win   wind-only         propertytsw    →  propertywin.json
    faw   flood AND wind     propertytsfaw  →  propertyfaw.json
    fow   flood OR wind      propertytsfow  →  propertyfow.json   (+ commercial*)
    bow   BRI OR wind        propertytsbow  →  propertybow.json
    baw   BRI AND wind       propertytsbaw  →  propertybaw.json

bow/baw mirror fow/faw but anchor the flood leg on the BRI-resilient flood
(derived from the bri ts rather than the raw flood spine) — the level the book
actually trades at. They are skipped when the bri ts is absent.

The wind leg has no gauge intermediary, so instead of a flood-propagation
timeseries we DERIVE the three ts dirs from the flood spine: the peril
timeseries generator re-stamps each event's flooded/exceeded_severe flags so
the existing hazard-curve pricer counts the peril of interest unchanged
(``count / num_storms × 10 000`` bps).

This stage runs AFTER the typhoon stage (which writes ``typhoon/damage/``).
It is skipped silently for catchments with no typhoon damage — the join input
the wind perils require.
"""

import time

from ..context import StageContext


def _damage_available(ctx: StageContext) -> bool:
    """True when the typhoon damage join input exists for this catchment."""
    damage_dir = ctx.input_dir / "typhoon" / "damage"
    return damage_dir.exists() and any(damage_dir.glob("EVT-*.json"))


def _peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "propertytsw", "propertytsfaw", "propertytsfow",
        "propertytsbow", "propertytsbaw",
        "propertywin", "propertyfaw", "propertyfow",
        "propertybow", "propertybaw",
    ))


def _commercial_peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "commercialtsw", "commercialtsfaw", "commercialtsfow",
        "commercialtsbow", "commercialtsbaw",
        "commercialwin", "commercialfaw", "commercialfow",
        "commercialbow", "commercialbaw",
    ))


# ----------------------------------------------------------------------
# Property
# ----------------------------------------------------------------------

def run_property_peril_ts(ctx: StageContext):
    """Derive propertytsw / propertytsfaw / propertytsfow from the flood spine."""
    if not ((ctx.run_all or _peril_requested(ctx)) and _damage_available(ctx)):
        return
    print("9. Deriving Property Peril Timeseries (win/faw/fow)...")
    from port.src.peril import PerilTimeseriesGenerator
    inputs = {
        "propertyts/": ctx.input_dir / "propertyts",
        "typhoon/damage/": ctx.input_dir / "typhoon" / "damage",
        "storm_sequences.json": ctx.input_dir / "storm_sequences.json",
    }
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = PerilTimeseriesGenerator(ctx.output_dir, verbose=ctx.args.verbose).generate()
    elapsed = time.time() - t_step
    if not r.get("available"):
        print("   (no typhoon damage — skipped)")
        return
    for mode, st in r["modes"].items():
        print(f"   {mode}: {st['files']} files  |  {st['triggers']} triggers  "
              f"|  {st['assets_with_trigger']} assets")
    ctx.record(
        step_name="property_peril_ts",
        generator="port.src.peril.PerilTimeseriesGenerator",
        inputs=inputs,
        input_hashes=pre,
        outputs={
            "propertytsw/": ctx.input_dir / "propertytsw",
            "propertytsfaw/": ctx.input_dir / "propertytsfaw",
            "propertytsfow/": ctx.input_dir / "propertytsfow",
            "propertytsbow/": ctx.input_dir / "propertytsbow",
            "propertytsbaw/": ctx.input_dir / "propertytsbaw",
        },
        parameters={"modes": list(r["modes"].keys())},
        elapsed_seconds=elapsed,
    )
    print()


def _run_property_peril_hc(ctx: StageContext, mode: str, label: str, step: str):
    args = ctx.args
    flag = {"win": "propertywin", "faw": "propertyfaw", "fow": "propertyfow",
            "bow": "propertybow", "baw": "propertybaw"}[mode]
    if not ((ctx.run_all or getattr(args, flag, False)) and _damage_available(ctx)):
        return
    ts_dir = {"win": "propertytsw", "faw": "propertytsfaw", "fow": "propertytsfow",
              "bow": "propertytsbow", "baw": "propertytsbaw"}[mode]
    out_file = {"win": "propertywin.json", "faw": "propertyfaw.json",
                "fow": "propertyfow.json", "bow": "propertybow.json",
                "baw": "propertybaw.json"}[mode]
    if not (ctx.input_dir / ts_dir).exists():
        return
    print(f"{step}. Building {label} Hazard Curves ({flag})...")
    inputs = {
        f"{ts_dir}/": ctx.input_dir / ts_dir,
        "gaugehc.json": ctx.input_dir / "gaugehc.json",
        "gauge.json": ctx.input_dir / "gauge.json",
    }
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyhc.PropertyHazardCurveGenerator(
        ctx.output_dir, verbose=args.verbose, mode=mode).generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} properties  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name=flag,
        generator=f"port.src.property.propertyhc.PropertyHazardCurveGenerator(mode={mode})",
        inputs=inputs,
        outputs={out_file: ctx.input_dir / out_file},
        parameters={"mode": mode},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_propertywin(ctx: StageContext):
    _run_property_peril_hc(ctx, "win", "Wind-Only (win)", "9a")


def run_propertyfaw(ctx: StageContext):
    _run_property_peril_hc(ctx, "faw", "Flood-AND-Wind (faw)", "9b")


def run_propertyfow(ctx: StageContext):
    _run_property_peril_hc(ctx, "fow", "Flood-OR-Wind (fow)", "9c")


def run_propertybow(ctx: StageContext):
    _run_property_peril_hc(ctx, "bow", "BRI-OR-Wind (bow)", "9c1")


def run_propertybaw(ctx: StageContext):
    _run_property_peril_hc(ctx, "baw", "BRI-AND-Wind (baw)", "9c2")


# ----------------------------------------------------------------------
# Commercial
# ----------------------------------------------------------------------

def run_commercial_peril_ts(ctx: StageContext):
    """Derive commercialtsw / commercialtsfaw / commercialtsfow."""
    run = (ctx.run_all and ctx.commercial_exists) or _commercial_peril_requested(ctx)
    if not run:
        return
    if not (_damage_available(ctx) and (ctx.input_dir / "commercialts").exists()):
        return
    print("9d. Deriving Commercial Peril Timeseries (win/faw/fow)...")
    from port.src.peril import CommercialPerilTimeseriesGenerator
    inputs = {
        "commercialts/": ctx.input_dir / "commercialts",
        "typhoon/damage/": ctx.input_dir / "typhoon" / "damage",
        "storm_sequences.json": ctx.input_dir / "storm_sequences.json",
    }
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = CommercialPerilTimeseriesGenerator(ctx.output_dir, verbose=ctx.args.verbose).generate()
    elapsed = time.time() - t_step
    if not r.get("available"):
        print("   (no typhoon damage — skipped)")
        return
    for mode, st in r["modes"].items():
        print(f"   {mode}: {st['files']} files  |  {st['triggers']} triggers  "
              f"|  {st['assets_with_trigger']} assets")
    ctx.record(
        step_name="commercial_peril_ts",
        generator="port.src.peril.CommercialPerilTimeseriesGenerator",
        inputs=inputs,
        input_hashes=pre,
        outputs={
            "commercialtsw/": ctx.input_dir / "commercialtsw",
            "commercialtsfaw/": ctx.input_dir / "commercialtsfaw",
            "commercialtsfow/": ctx.input_dir / "commercialtsfow",
            "commercialtsbow/": ctx.input_dir / "commercialtsbow",
            "commercialtsbaw/": ctx.input_dir / "commercialtsbaw",
        },
        parameters={"modes": list(r["modes"].keys())},
        elapsed_seconds=elapsed,
    )
    print()


def _run_commercial_peril_hc(ctx: StageContext, mode: str, label: str, step: str):
    args = ctx.args
    flag = {"win": "commercialwin", "faw": "commercialfaw", "fow": "commercialfow",
            "bow": "commercialbow", "baw": "commercialbaw"}[mode]
    run = (getattr(args, flag, False)
           or (ctx.run_all and ctx.commercial_exists))
    if not (run and _damage_available(ctx)):
        return
    ts_dir = {"win": "commercialtsw", "faw": "commercialtsfaw",
              "fow": "commercialtsfow", "bow": "commercialtsbow",
              "baw": "commercialtsbaw"}[mode]
    out_file = {"win": "commercialwin.json", "faw": "commercialfaw.json",
                "fow": "commercialfow.json", "bow": "commercialbow.json",
                "baw": "commercialbaw.json"}[mode]
    if not (ctx.input_dir / ts_dir).exists():
        return
    print(f"{step}. Building {label} Commercial Hazard Curves ({flag})...")
    inputs = {
        f"{ts_dir}/": ctx.input_dir / ts_dir,
        "gaugehc.json": ctx.input_dir / "gaugehc.json",
        "gauge.json": ctx.input_dir / "gauge.json",
    }
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialHazardCurveGenerator(
        ctx.output_dir, verbose=args.verbose, mode=mode).generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} commercial assets  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name=flag,
        generator=f"port.src.commercial.CommercialHazardCurveGenerator(mode={mode})",
        inputs=inputs,
        outputs={out_file: ctx.input_dir / out_file},
        parameters={"mode": mode},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercialwin(ctx: StageContext):
    _run_commercial_peril_hc(ctx, "win", "Wind-Only (win)", "9e")


def run_commercialfaw(ctx: StageContext):
    _run_commercial_peril_hc(ctx, "faw", "Flood-AND-Wind (faw)", "9f")


def run_commercialfow(ctx: StageContext):
    _run_commercial_peril_hc(ctx, "fow", "Flood-OR-Wind (fow)", "9g")


def run_commercialbow(ctx: StageContext):
    _run_commercial_peril_hc(ctx, "bow", "BRI-OR-Wind (bow)", "9g1")


def run_commercialbaw(ctx: StageContext):
    _run_commercial_peril_hc(ctx, "baw", "BRI-AND-Wind (baw)", "9g2")


# ----------------------------------------------------------------------
# Re-attach spread decomposition (canonical peril fan from win/faw/fow)
# ----------------------------------------------------------------------
#
# attach_spread_decomposition runs in the hazardcurves stage (step 8), BEFORE
# the win/faw/fow files exist (step 9). Re-run it now so the peril-outcomes fan
# is sourced canonically from the freshly-written scenario files rather than the
# damage-join fallback. Idempotent — it simply re-reads every basis file and
# rewrites the decomposition block on the normal hc file.

def run_property_peril_decomposition(ctx: StageContext):
    if not (ctx.output_dir / "propertyhc.json").exists():
        return
    if not any((ctx.output_dir / f).exists()
               for f in ("propertywin.json", "propertyfaw.json", "propertyfow.json",
                         "propertybow.json", "propertybaw.json")):
        return
    print("9h. Re-attaching Spread Decomposition (peril fan from win/faw/fow/bow/baw)...")
    gen = ctx.propertyhc.PropertyHazardCurveGenerator(
        ctx.output_dir, verbose=ctx.args.verbose)
    n = gen.attach_spread_decomposition()
    print(f"   {n} properties decomposed")
    print()


def run_commercial_peril_decomposition(ctx: StageContext):
    if not (ctx.output_dir / "commercialhc.json").exists():
        return
    if not any((ctx.output_dir / f).exists()
               for f in ("commercialwin.json", "commercialfaw.json", "commercialfow.json",
                         "commercialbow.json", "commercialbaw.json")):
        return
    print("9i. Re-attaching Commercial Spread Decomposition (peril fan from win/faw/fow/bow/baw)...")
    gen = ctx.commercial_gen.CommercialHazardCurveGenerator(
        ctx.output_dir, verbose=ctx.args.verbose)
    n = gen.attach_spread_decomposition()
    print(f"   {n} commercial assets decomposed")
    print()


def run_all(ctx: StageContext):
    run_property_peril_ts(ctx)
    run_propertywin(ctx)
    run_propertyfaw(ctx)
    run_propertyfow(ctx)
    run_propertybow(ctx)
    run_propertybaw(ctx)
    run_property_peril_decomposition(ctx)
    run_commercial_peril_ts(ctx)
    run_commercialwin(ctx)
    run_commercialfaw(ctx)
    run_commercialfow(ctx)
    run_commercialbow(ctx)
    run_commercialbaw(ctx)
    run_commercial_peril_decomposition(ctx)
