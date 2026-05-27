# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Hazard-curve stages: property HC (8, 8a, 8b, 8c) + commercial HC
(8d, 8e, 8f, 8g)."""

import time

from ..context import StageContext


def _hc_inputs(ctx: StageContext, ts_dir: str) -> dict:
    return {
        f"{ts_dir}/": ctx.input_dir / ts_dir,
        "gaugehc.json": ctx.input_dir / "gaugehc.json",
        "gauge.json": ctx.input_dir / "gauge.json",
    }


def run_propertyhc(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertyhc):
        return
    if ctx.strict_block("propertyhc"):
        raise SystemExit
    print("8. Building Property Hazard Curves + PRS Pricing...")
    inputs = _hc_inputs(ctx, "propertyts")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyhc.PropertyHazardCurveGenerator(ctx.output_dir, verbose=args.verbose).generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    processed = r.get('properties_processed', '?')
    skipped = r.get('properties_skipped', 0)
    avg_spread = r.get('avg_spread_bps', 0)
    avg_tr = r.get('avg_transmission_rate', 0) * 100
    print(f"   {total} properties  |  {processed} processed  |  {skipped} skipped")
    print(f"   avg spread: {avg_spread:.1f} bps  |  avg transmission: {avg_tr:.1f}%")
    ctx.record(
        step_name="propertyhc",
        generator="port.src.property.propertyhc.PropertyHazardCurveGenerator",
        inputs=inputs,
        input_hashes=pre,
        outputs={"propertyhc.json": ctx.input_dir / "propertyhc.json"},
        parameters={},
        elapsed_seconds=elapsed,
        stale_name="propertyhc",
    )
    print()


def run_propertyshd(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertyshd):
        return
    print("8a. Building Synthetic Distance Hazard Curves (propertyshd)...")
    inputs = _hc_inputs(ctx, "propertytsd")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyhc.PropertyHazardCurveGenerator(ctx.output_dir, verbose=args.verbose, mode="shd").generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} properties  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name="propertyshd",
        generator="port.src.property.propertyhc.PropertyHazardCurveGenerator(mode=shd)",
        inputs=inputs,
        outputs={"propertyshd.json": ctx.input_dir / "propertyshd.json"},
        parameters={"mode": "shd"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_propertyshe(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertyshe):
        return
    print("8b. Building Synthetic Elevation Hazard Curves (propertyshe)...")
    inputs = _hc_inputs(ctx, "propertytse")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyhc.PropertyHazardCurveGenerator(ctx.output_dir, verbose=args.verbose, mode="she").generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} properties  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name="propertyshe",
        generator="port.src.property.propertyhc.PropertyHazardCurveGenerator(mode=she)",
        inputs=inputs,
        outputs={"propertyshe.json": ctx.input_dir / "propertyshe.json"},
        parameters={"mode": "she"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_property_spread_decomposition(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or (args.propertyhc and args.propertyshd and args.propertyshe)):
        return
    paths = [ctx.output_dir / f for f in ('propertyhc.json', 'propertyshd.json', 'propertyshe.json')]
    if not all(p.exists() for p in paths):
        return
    print("8c. Attaching Spread Decomposition to propertyhc.json...")
    gen = ctx.propertyhc.PropertyHazardCurveGenerator(ctx.output_dir, verbose=args.verbose)
    n = gen.attach_spread_decomposition()
    print(f"   {n} properties decomposed")
    print()


def run_commercialhc(ctx: StageContext):
    args = ctx.args
    if not (args.commercialhc or
            (ctx.run_all and ctx.commercial_exists and (ctx.input_dir / 'commercialts').exists())):
        return
    print("8d. Building Commercial Hazard Curves + PRS Pricing...")
    inputs = _hc_inputs(ctx, "commercialts")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialHazardCurveGenerator(ctx.output_dir, verbose=args.verbose).generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    processed = r.get('properties_processed', '?')
    skipped = r.get('properties_skipped', 0)
    avg_spread = r.get('avg_spread_bps', 0)
    avg_tr = r.get('avg_transmission_rate', 0) * 100
    print(f"   {total} commercial assets  |  {processed} processed  |  {skipped} skipped")
    print(f"   avg spread: {avg_spread:.1f} bps  |  avg transmission: {avg_tr:.1f}%")
    ctx.record(
        step_name="commercialhc",
        generator="port.src.commercial.CommercialHazardCurveGenerator",
        inputs=inputs,
        input_hashes=pre,
        outputs={"commercialhc.json": ctx.input_dir / "commercialhc.json"},
        parameters={},
        elapsed_seconds=elapsed,
        stale_name="commercialhc",
    )
    print()


def run_commercialshd(ctx: StageContext):
    args = ctx.args
    if not (args.commercialshd or
            (ctx.run_all and ctx.commercial_exists and (ctx.input_dir / 'commercialtsd').exists())):
        return
    print("8e. Building Synthetic Distance Hazard Curves (commercialshd)...")
    inputs = _hc_inputs(ctx, "commercialtsd")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialHazardCurveGenerator(ctx.output_dir, verbose=args.verbose, mode="shd").generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} commercial assets  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name="commercialshd",
        generator="port.src.commercial.CommercialHazardCurveGenerator(mode=shd)",
        inputs=inputs,
        outputs={"commercialshd.json": ctx.input_dir / "commercialshd.json"},
        parameters={"mode": "shd"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercialshe(ctx: StageContext):
    args = ctx.args
    if not (args.commercialshe or
            (ctx.run_all and ctx.commercial_exists and (ctx.input_dir / 'commercialtse').exists())):
        return
    print("8f. Building Synthetic Elevation Hazard Curves (commercialshe)...")
    inputs = _hc_inputs(ctx, "commercialtse")
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialHazardCurveGenerator(ctx.output_dir, verbose=args.verbose, mode="she").generate()
    elapsed = time.time() - t_step
    total = r.get('total_properties', '?')
    avg_spread = r.get('avg_spread_bps', 0)
    print(f"   {total} commercial assets  |  avg spread: {avg_spread:.1f} bps")
    ctx.record(
        step_name="commercialshe",
        generator="port.src.commercial.CommercialHazardCurveGenerator(mode=she)",
        inputs=inputs,
        outputs={"commercialshe.json": ctx.input_dir / "commercialshe.json"},
        parameters={"mode": "she"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercial_spread_decomposition(ctx: StageContext):
    args = ctx.args
    if not ((args.commercialhc and args.commercialshd and args.commercialshe)
            or (ctx.run_all and ctx.commercial_exists)):
        return
    paths = [ctx.output_dir / f for f in
             ('commercialhc.json', 'commercialshd.json', 'commercialshe.json')]
    if not all(p.exists() for p in paths):
        return
    print("8g. Attaching Spread Decomposition to commercialhc.json...")
    gen = ctx.commercial_gen.CommercialHazardCurveGenerator(ctx.output_dir, verbose=args.verbose)
    n = gen.attach_spread_decomposition()
    print(f"   {n} commercial assets decomposed")
    print()


def run_all(ctx: StageContext):
    run_propertyhc(ctx)
    run_propertyshd(ctx)
    run_propertyshe(ctx)
    run_property_spread_decomposition(ctx)
    run_commercialhc(ctx)
    run_commercialshd(ctx)
    run_commercialshe(ctx)
    run_commercial_spread_decomposition(ctx)
