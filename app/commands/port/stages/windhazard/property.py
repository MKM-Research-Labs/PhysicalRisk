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

"""Property wind-coupled peril timeseries + hazard-curve stages."""

import time

from ...context import StageContext
from ._helpers import _damage_available, _peril_requested
from ._placeholders import write_peril_placeholders


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


# Re-attach spread decomposition (canonical peril fan from win/faw/fow).
#
# attach_spread_decomposition runs in the hazardcurves stage (step 8), BEFORE
# the win/faw/fow files exist (step 9). Re-run it now so the peril-outcomes fan
# is sourced canonically from the freshly-written scenario files rather than the
# damage-join fallback. Idempotent — it simply re-reads every basis file and
# rewrites the decomposition block on the normal hc file.

def run_property_peril_placeholders(ctx: StageContext):
    """No-typhoon fallback: write zero-event scenario placeholders.

    When the typhoon ensemble has not run, the real win/faw/fow/bow/baw stages
    skip, so the wind UI tabs would 404 (or serve stale files from an earlier
    typhoon run). Project the degenerate peril fan already embedded in
    propertyhc/propertybri into the standalone scenario files so the routes
    serve consistent zero-event data. No-op when typhoon damage IS present
    (the real files were generated) or when no property peril output is wanted.
    """
    if _damage_available(ctx):
        return
    if not (ctx.run_all or _peril_requested(ctx)):
        return
    if not (ctx.output_dir / "propertyhc.json").exists():
        return
    print("9h. Writing zero-event Property peril placeholders (no typhoon)...")
    write_peril_placeholders(ctx.output_dir, "property")
    print()


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
