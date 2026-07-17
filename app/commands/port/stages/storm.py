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

"""Storm + hazard stages: multi-storm stress test (5) and gauge hazard
curves (6)."""

import time
from pathlib import Path

from config import config

from ..context import StageContext


def run_stressm(ctx: StageContext):
    args = ctx.args
    # --gaugets is now handled by stressm (generates base sim + storm responses).
    if not ((ctx.run_all and not args.nostress) or args.stressm or args.gaugets):
        return
    if ctx.strict_block("stressm"):
        raise SystemExit
    print("5. Multi-Storm Sequences + Gaugets + Stress Storms...")
    from port.src.stressm import generate_stressm, GAUGE_SUMMARY_FILENAME
    from port.src.storm_multi.utils.serialization import SEQUENCES_FILENAME, SUMMARY_FILENAME

    # Clean ALL classifiers — they were trained against old storm data
    # and must be retrained per-gauge via the UI after a fresh port run.
    _clean_dirs = [
        Path(config.get_classifiers_dir()),
        Path(config.get_output_dir()) / "stressm",
        ctx.output_dir / "stressm" if ctx.output_dir else None,
    ]
    for _cls_dir in _clean_dirs:
        if _cls_dir is None or not _cls_dir.exists():
            continue
        _stale = list(_cls_dir.glob("*.joblib"))
        if _stale:
            print(f"  Cleaning {len(_stale)} stale classifier(s) from {_cls_dir.name}/...")
            for jf in _stale:
                jf.unlink()
        _summary_path = _cls_dir / "training_summary.json"
        if _summary_path.exists():
            _summary_path.unlink()
            print(f"  Removed training_summary.json from {_cls_dir.name}/")

    inputs = {"gauge.json": ctx.input_dir / "gauge.json",
              "gaugehd/": ctx.input_dir / "gaugehd"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    summary = generate_stressm(
        input_dir=ctx.output_dir,
        output_dir=config.get_output_dir(),
        count=args.num_sims,
        catchment_id=ctx.catchment,
        seed=42,
        verbose=args.verbose,
        gauge_id=args.gauge_id,
        train_classifier=False,
    )
    elapsed = time.time() - t_step

    tc = summary.get("type_counts", {})
    tc_str = "  ".join(f"{k}: {v:,}" for k, v in sorted(tc.items()))
    n = summary["num_sequences"]
    ng = summary["num_gauges"]
    rt_elapsed = summary.get("elapsed_seconds", 0)

    print(f'\n{"=" * 60}')
    print(f' Multi-Storm Stress Summary')
    print(f'{"=" * 60}')
    print(f' Sequences generated : {n:,}')
    print(f' Types               : {tc_str}')
    print(f' Gauges              : {ng}')
    print(f' Alert sequences     : {summary["alert_sequences"]:,}')
    print(f' Warning sequences   : {summary["warning_sequences"]:,}')
    print(f' Severe sequences    : {summary["severe_sequences"]:,}')
    print(f' Elapsed             : {rt_elapsed:.0f}s ({rt_elapsed / 60:.1f} min)')
    print(f'{"=" * 60}')
    print(f'   Output files:')
    print(f'   gaugets/ (base simulation + storm responses)')
    print(f'   stress_storms/ (per-storm files)')
    print(f'   {SEQUENCES_FILENAME}')
    print(f'   {SUMMARY_FILENAME}')
    print(f'   {GAUGE_SUMMARY_FILENAME}')
    ctx.record(
        step_name="stressm",
        generator="port.src.stressm.generate_stressm",
        inputs=inputs,
        outputs={
            "gaugets/": ctx.input_dir / "gaugets",
            "stress_storms/": ctx.input_dir / "stress_storms",
            "storm_sequences.json": ctx.input_dir / "storm_sequences.json",
            "sequence_gauge/": ctx.input_dir / "sequence_gauge",
        },
        parameters={"num_storms": args.num_sims},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="stressm",
    )
    print()


def run_hazard(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.hazard):
        return
    if ctx.strict_block("hazard"):
        raise SystemExit
    print("6. Building Hazard Curves...")
    inputs = {"gauge.json": ctx.input_dir / "gauge.json",
              "gaugets/": ctx.input_dir / "gaugets"}
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.hazard.build_hazard_curves(
        catchment_id=ctx.catchment,
        distribution=args.distribution, verbose=args.verbose,
    )
    elapsed = time.time() - t_step
    s = r.get('summary', {})
    n_g = s.get('num_gauges', '?')
    n_s = s.get('num_storms', '?')
    p_alert = s.get('avg_annual_prob_alert', 0) * 100
    p_warning = s.get('avg_annual_prob_warning', 0) * 100
    p_severe = s.get('avg_annual_prob_severe', 0) * 100
    print(f"   {n_g} gauge curves  ({n_s:,} individual storms  |  dist: {args.distribution.upper()})")
    print(f"   avg annual P(alert): {p_alert:.2f}%  "
          f"P(warning): {p_warning:.2f}%  "
          f"P(severe): {p_severe:.2f}%")
    ctx.record(
        step_name="hazard",
        generator="port.src.hazard.build_hazard_curves",
        inputs=inputs,
        outputs={"gaugehc.json": ctx.input_dir / "gaugehc.json",
                 "gaugets/": ctx.input_dir / "gaugets"},
        parameters={"distribution": args.distribution},
        input_hashes=pre,
        elapsed_seconds=elapsed,
        stale_name="hazard",
    )
    print()


def run_all(ctx: StageContext):
    run_stressm(ctx)
    run_hazard(ctx)
