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

"""Portfolio-data stages: gauges (1, 1.5), properties (2), mortgages (3),
commercial (3a, 3b), gauge historical data (4)."""

import time

from ..context import StageContext


def run_gauges(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.gauges):
        return
    if ctx.strict_block("gauges"):
        raise SystemExit
    print("1. Generating Gauges...")
    t_step = time.time()
    r = ctx.gauge.GaugePortfolioGenerator(verbose=args.verbose).generate(args.num_gauges)
    elapsed = time.time() - t_step
    n = len(r['data']['flood_gauges'])
    stats = r.get('processing_stats', {})
    ok = stats.get('successful_gauges', n)
    print(f"   {n} gauges generated  ({ok}/{stats.get('total_gauges', n)} successful)"
          f"  →  gauge.json")
    ctx.record(
        step_name="gauges",
        generator="port.src.gauge.GaugePortfolioGenerator",
        inputs={},
        outputs={"gauge.json": ctx.input_dir / "gauge.json"},
        parameters={"num_gauges": args.num_gauges},
        elapsed_seconds=elapsed,
        stale_name="gauges",
    )
    print()


def run_synthetic_gauges(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.gauges or args.properties):
        return
    from port.src.gauge.synthetic import SyntheticGaugeGenerator
    print("1.5 Generating Synthetic Gauges...")
    inputs = {"gauge.json": ctx.input_dir / "gauge.json"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = SyntheticGaugeGenerator(ctx.output_dir).generate(count=args.num_properties)
    elapsed = time.time() - t_step
    n = r.get("count", 0)
    print(f"   {n} synthetic gauges  →  gauge.json (updated)")
    ctx.record(
        step_name="synthetic_gauges",
        generator="port.src.gauge.synthetic.SyntheticGaugeGenerator",
        inputs=inputs,
        outputs={"gauge.json": ctx.input_dir / "gauge.json"},
        parameters={"count": args.num_properties},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_properties(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.properties):
        return
    if ctx.strict_block("properties"):
        raise SystemExit
    print("2. Generating Properties...")
    inputs = {"gauge.json": ctx.input_dir / "gauge.json"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.prop_gen.PropertyPortfolioGenerator().generate(args.num_properties)
    elapsed = time.time() - t_step
    n = len(r['data']['properties'])
    stats = r.get('processing_stats', {})
    ok = stats.get('successful_properties', n)
    print(f"   {n} properties generated  ({ok}/{stats.get('total_properties', n)} successful)"
          f"  →  property.json")
    ctx.record(
        step_name="properties",
        generator="port.src.property.PropertyPortfolioGenerator",
        inputs=inputs,
        outputs={"property.json": ctx.input_dir / "property.json"},
        parameters={"num_properties": args.num_properties},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="properties",
    )
    print()


def run_mortgages(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.mortgages):
        return
    if ctx.strict_block("mortgages"):
        raise SystemExit
    print("3. Generating Mortgages...")
    inputs = {"property.json": ctx.input_dir / "property.json"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.mortgage.MortgagePortfolioGenerator().generate()
    elapsed = time.time() - t_step
    n = len(r['data']['mortgages'])
    stats = r.get('processing_stats', {})
    ok = stats.get('successful_mortgages', n)
    print(f"   {n} mortgages generated  ({ok}/{stats.get('total_mortgages', n)} successful)"
          f"  →  loan.json")
    ctx.record(
        step_name="mortgages",
        generator="port.src.mortgage.MortgagePortfolioGenerator",
        inputs=inputs,
        outputs={"loan.json": ctx.input_dir / "loan.json"},
        parameters={},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="mortgages",
    )
    print()


def run_commercial_portfolio(ctx: StageContext):
    """Commercial assets + commercial loans (steps 3a + 3b).

    Runs under ``--all`` (like the property portfolio) or when ``--commercial``
    is set, so ``-nc/--num-commercial`` takes effect in a default port run
    rather than silently leaving a stale commercial.json that the downstream
    commercial hazard stages then build on.
    """
    args = ctx.args
    if not (ctx.run_all or args.commercial):
        return
    print("3a. Generating Commercial Portfolio...")
    t_start = time.time()
    r = ctx.commercial_gen.CommercialPortfolioGenerator(
        verbose=False).generate(args.num_commercial)
    n = len(r['data']['commercial_assets'])
    stats = r.get('processing_stats', {})
    ok = stats.get('successful_assets', n)
    type_counts = {}
    for a in r['data']['commercial_assets']:
        t = a['CommercialAsset']['CommercialAttributes']['CommercialType']
        type_counts[t] = type_counts.get(t, 0) + 1
    mix = ", ".join(f"{k}: {v}" for k, v in sorted(type_counts.items()))
    print(f"   {n} commercial assets generated  ({ok}/{stats.get('total_assets', n)} successful)"
          f"  →  commercial.json")
    print(f"   Type mix: {mix}")

    print("3b. Generating Commercial Loans...")
    rl = ctx.commercial_loan_gen_cls(verbose=False).generate()
    elapsed = time.time() - t_start
    nl = len(rl['data']['commercial_loans'])
    print(f"   {nl} commercial loans generated  →  commercial_loan.json")
    ctx.record(
        step_name="commercial",
        generator="port.src.commercial.CommercialPortfolioGenerator",
        inputs={},
        outputs={
            "commercial.json": ctx.input_dir / "commercial.json",
            "commercial_loan.json": ctx.input_dir / "commercial_loan.json",
        },
        parameters={"num_commercial": args.num_commercial},
        elapsed_seconds=elapsed,
        stale_name="commercial",
    )
    print()


def run_gaugehd(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.gaugehd):
        return
    if ctx.strict_block("gaugehd"):
        raise SystemExit
    print("4. Generating Gauge Historical Data...")
    inputs = {"gauge.json": ctx.input_dir / "gauge.json"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    files = ctx.gaugehd.generate_all_gauge_histories(years=args.history_years)
    elapsed = time.time() - t_step
    n = len(files) if files else 0
    print(f"   {n} gauge histories  ×  {args.history_years} years  →  gaugehd/")
    ctx.record(
        step_name="gaugehd",
        generator="port.src.gauge.gaugehd",
        inputs=inputs,
        outputs={"gaugehd/": ctx.input_dir / "gaugehd"},
        parameters={"history_years": args.history_years},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="gaugehd",
    )
    print()


def run_all(ctx: StageContext):
    """Run all portfolio stages in order."""
    run_gauges(ctx)
    run_synthetic_gauges(ctx)
    run_properties(ctx)
    run_mortgages(ctx)
    run_commercial_portfolio(ctx)
    run_gaugehd(ctx)
