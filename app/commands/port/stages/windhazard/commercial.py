# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Commercial wind-coupled peril timeseries + hazard-curve stages."""

import time

from ...context import StageContext
from ._helpers import _commercial_peril_requested, _damage_available
from ._placeholders import write_peril_placeholders


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


def run_commercial_peril_placeholders(ctx: StageContext):
    """No-typhoon fallback: write zero-event commercial scenario placeholders.

    Mirror of run_property_peril_placeholders for commercial assets. No-op when
    typhoon damage is present, when commercial isn't part of the run, or when
    commercialhc.json is absent.
    """
    if _damage_available(ctx):
        return
    if not ((ctx.run_all and ctx.commercial_exists)
            or _commercial_peril_requested(ctx)):
        return
    if not (ctx.output_dir / "commercialhc.json").exists():
        return
    print("9i. Writing zero-event Commercial peril placeholders (no typhoon)...")
    write_peril_placeholders(ctx.output_dir, "commercial")
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
