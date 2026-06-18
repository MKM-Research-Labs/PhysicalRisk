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

"""Time-series stages: property TS (7, 7a, 7b, 7f) + commercial TS
(7c, 7d, 7e, 7g). The ``b`` suffix (7f/7g) is the BRI-adjusted-floor run."""

import time

from ..context import StageContext


_PROP_INPUTS = lambda ctx: {
    "property.json": ctx.input_dir / "property.json",
    "gauge.json": ctx.input_dir / "gauge.json",
    "gaugets/": ctx.input_dir / "gaugets",
}


_COMM_INPUTS = lambda ctx: {
    "commercial.json": ctx.input_dir / "commercial.json",
    "gauge.json": ctx.input_dir / "gauge.json",
    "gaugets/": ctx.input_dir / "gaugets",
}


def _summary_line(r, label):
    total = r.get('total_properties', '?')
    flooded = r.get('properties_with_floods', '?')
    events = r.get('total_flood_events', '?')
    print(f"   {total} {label}  |  {flooded} with flood events  |  {events:,} total events")


def run_propertyts(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertyts):
        return
    if ctx.strict_block("propertyts"):
        raise SystemExit
    print("7. Generating Property Flood Time Series...")
    inputs = _PROP_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyts.PropertyTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose).generate()
    elapsed = time.time() - t_step
    _summary_line(r, "properties")
    max_d = r.get('max_depth_m', 0)
    max_dr = r.get('max_damage_ratio', 0)
    print(f"   max depth: {max_d:.2f}m  |  max damage ratio: {max_dr:.1%}")
    ctx.record(
        step_name="propertyts",
        generator="port.src.property.propertyts.PropertyTimeSeriesGenerator",
        inputs=inputs,
        outputs={"propertyts/": ctx.input_dir / "propertyts"},
        parameters={},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="propertyts",
    )
    print()


def run_propertytsd(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertytsd):
        return
    print("7a. Generating Synthetic Distance Timeseries (propertytsd)...")
    inputs = _PROP_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyts.PropertyTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="shd").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "properties")
    ctx.record(
        step_name="propertytsd",
        generator="port.src.property.propertyts.PropertyTimeSeriesGenerator(mode=shd)",
        inputs=inputs,
        outputs={"propertytsd/": ctx.input_dir / "propertytsd"},
        parameters={"mode": "shd"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_propertytse(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertytse):
        return
    print("7b. Generating Synthetic Elevation Timeseries (propertytse)...")
    inputs = _PROP_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyts.PropertyTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="she").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "properties")
    ctx.record(
        step_name="propertytse",
        generator="port.src.property.propertyts.PropertyTimeSeriesGenerator(mode=she)",
        inputs=inputs,
        outputs={"propertytse/": ctx.input_dir / "propertytse"},
        parameters={"mode": "she"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_propertytsb(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.propertytsb):
        return
    print("7f. Generating BRI-Adjusted Floor Timeseries (propertytsb)...")
    inputs = _PROP_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.propertyts.PropertyTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="bri").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "properties")
    ctx.record(
        step_name="propertytsb",
        generator="port.src.property.propertyts.PropertyTimeSeriesGenerator(mode=bri)",
        inputs=inputs,
        outputs={"propertytsb/": ctx.input_dir / "propertytsb"},
        parameters={"mode": "bri"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercialts(ctx: StageContext):
    args = ctx.args
    if not (args.commercialts or (ctx.run_all and ctx.commercial_exists)):
        return
    print("7c. Generating Commercial Flood Time Series...")
    inputs = _COMM_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose).generate()
    elapsed = time.time() - t_step
    _summary_line(r, "commercial assets")
    print(f"   max depth: {r.get('max_depth_m', 0):.2f}m")
    ctx.record(
        step_name="commercialts",
        generator="port.src.commercial.CommercialTimeSeriesGenerator",
        inputs=inputs,
        outputs={"commercialts/": ctx.input_dir / "commercialts"},
        parameters={},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="commercialts",
    )
    print()


def run_commercialtsd(ctx: StageContext):
    args = ctx.args
    if not (args.commercialtsd or (ctx.run_all and ctx.commercial_exists)):
        return
    print("7d. Generating Synthetic Distance Timeseries (commercialtsd)...")
    inputs = _COMM_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="shd").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "commercial assets")
    ctx.record(
        step_name="commercialtsd",
        generator="port.src.commercial.CommercialTimeSeriesGenerator(mode=shd)",
        inputs=inputs,
        outputs={"commercialtsd/": ctx.input_dir / "commercialtsd"},
        parameters={"mode": "shd"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercialtse(ctx: StageContext):
    args = ctx.args
    if not (args.commercialtse or (ctx.run_all and ctx.commercial_exists)):
        return
    print("7e. Generating Synthetic Elevation Timeseries (commercialtse)...")
    inputs = _COMM_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="she").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "commercial assets")
    ctx.record(
        step_name="commercialtse",
        generator="port.src.commercial.CommercialTimeSeriesGenerator(mode=she)",
        inputs=inputs,
        outputs={"commercialtse/": ctx.input_dir / "commercialtse"},
        parameters={"mode": "she"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_commercialtsb(ctx: StageContext):
    args = ctx.args
    if not (args.commercialtsb or (ctx.run_all and ctx.commercial_exists)):
        return
    print("7g. Generating BRI-Adjusted Floor Timeseries (commercialtsb)...")
    inputs = _COMM_INPUTS(ctx)
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    r = ctx.commercial_gen.CommercialTimeSeriesGenerator(ctx.output_dir, verbose=args.verbose, mode="bri").generate()
    elapsed = time.time() - t_step
    _summary_line(r, "commercial assets")
    ctx.record(
        step_name="commercialtsb",
        generator="port.src.commercial.CommercialTimeSeriesGenerator(mode=bri)",
        inputs=inputs,
        outputs={"commercialtsb/": ctx.input_dir / "commercialtsb"},
        parameters={"mode": "bri"},
        elapsed_seconds=elapsed,
        input_hashes=pre,
    )
    print()


def run_all(ctx: StageContext):
    run_propertyts(ctx)
    run_propertytsd(ctx)
    run_propertytse(ctx)
    run_propertytsb(ctx)
    run_commercialts(ctx)
    run_commercialtsd(ctx)
    run_commercialtse(ctx)
    run_commercialtsb(ctx)
