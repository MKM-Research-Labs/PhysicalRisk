#!/usr/bin/env python3

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

"""
Port command - Portfolio data generation.
"""

from config import config


def register_parser(subparsers):
    """Register the 'port' subcommand."""
    sp = subparsers.add_parser("port", help="Generate synthetic portfolio data")
    sp.add_argument("--gauges", "--ga", action="store_true")
    sp.add_argument("--properties", "--pr", action="store_true")
    sp.add_argument("--mortgages", "--mo", action="store_true")
    sp.add_argument("--gaugets", "--gt", action="store_true")
    sp.add_argument("--gaugehd", "--hd", action="store_true")
    sp.add_argument("--hazard", "--hz", action="store_true")
    sp.add_argument("--propertyts", "--pt", action="store_true")
    sp.add_argument("--propertytsd", action="store_true",
                    help="Synthetic distance timeseries (elevation diff = 0)")
    sp.add_argument("--propertytse", action="store_true",
                    help="Synthetic elevation timeseries (distance = 0)")
    sp.add_argument("--propertyhc", "--phc", action="store_true")
    sp.add_argument("--propertyshd", action="store_true",
                    help="Synthetic distance hazard curves (elevation diff = 0)")
    sp.add_argument("--propertyshe", action="store_true",
                    help="Synthetic elevation hazard curves (distance = 0)")
    sp.add_argument("--counterparties", "--ctpy", action="store_true")
    sp.add_argument("--blotter", "--bl", action="store_true")
    sp.add_argument("--stressm", action="store_true",
                    help="Multi-storm stress test (sequence-based, replaces --stress)")
    sp.add_argument("--gauge-id", "--gid", type=str, default=None,
                    help="Restrict --stressm to a single gauge ID")
    sp.add_argument("--pdf", action="store_true",
                    help="Generate portfolio report PDF after generation")
    sp.add_argument("--all", "-a", action="store_true", help="Run all segments")
    sp.add_argument("--nostress", action="store_true",
                    help="Skip stress test generation when running --all (step 12)")
    sp.add_argument("--strict", action="store_true",
                    help="Refuse to run if upstream data is stale (BCBS 239 lineage guard)")
    sp.add_argument("--verbose", "-v", action="store_true")
    sp.add_argument("--num-properties", "-np", type=int, default=200)
    sp.add_argument("--num-gauges", "-ng", type=int, default=52)
    sp.add_argument("--num-storms", "-ns", type=int, default=20000)
    sp.add_argument("--simulation-hours", type=int, default=168)
    sp.add_argument("--history-years", "-hy", type=int, default=50)
    sp.add_argument("--tail-weight", "-tw", type=float, default=2.0)
    sp.add_argument("--distribution", "-d", choices=["gev", "gumbel"], default="gev")
    sp.add_argument("--repair-manifest", action="store_true",
                    help="Re-hash all pipeline artifacts and rebuild a consistent manifest")
    sp.set_defaults(func=cmd_port)


def cmd_port(args):
    """Generate synthetic portfolio data."""
    catchment = 'thames'
    config.catchment_id = catchment
    output_dir = config.get_input_dir()
    input_dir = output_dir  # alias for clarity in lineage mappings

    # --- Repair manifest (standalone mode) --------------------------------
    # Checked before heavy imports so it works without pandas/scipy etc.
    if getattr(args, 'repair_manifest', False):
        try:
            from lineage.manifest import repair_manifest
        except ImportError:
            print("ERROR: lineage package not available")
            return
        print(f"\nMKM Portfolio Generator — Manifest Repair")
        print(f"Catchment: {catchment}")
        print(f"Data dir:  {output_dir}\n")
        result = repair_manifest(data_dir=output_dir)
        for step in result["repaired"]:
            print(f"  ✓ {step}")
        for step in result["skipped"]:
            print(f"  ⚠ {step} (outputs missing — skipped)")
        print(f"\nRepaired {len(result['repaired'])} steps, "
              f"skipped {len(result['skipped'])}.")
        return

    import time
    from port.src import gauge, mortgage, hazard, counterparty
    from port.src import property as prop_gen
    from port.src.gauge import gaugehd
    from port.src.property import propertyts, propertyhc

    try:
        from lineage.manifest import record_step, get_current_run_id, pre_hash_inputs
        from lineage.validation import (
            check_inputs_fresh, get_stale_downstream, resolve_prerequisites,
        )
    except ImportError:
        record_step = None
        get_current_run_id = None
        pre_hash_inputs = None
        check_inputs_fresh = None
        get_stale_downstream = None
        resolve_prerequisites = None

    run_id = None
    if get_current_run_id is not None:
        try:
            run_id = get_current_run_id()
        except Exception:
            pass

    print(f"\nMKM Portfolio Generator")
    print(f"Catchment: {catchment}")
    print(f"Output: {output_dir}\n")
    
    # Determine which segments to run
    segment_flags = [
        args.gauges, args.properties, args.mortgages,
        args.gaugets, args.gaugehd, args.hazard,
        args.propertyts, args.propertytsd, args.propertytse,
        args.propertyhc, args.propertyshd, args.propertyshe,
        args.counterparties, args.blotter, args.stressm,
    ]
    run_all = args.all or not any(segment_flags)

    # --- Auto-prerequisite resolution (single-step mode only) -----------
    # When running individual steps (not --all, not --strict), detect
    # missing or stale upstream steps and enable their flags so they
    # execute automatically in the existing sequential order.
    if not run_all and not args.strict and resolve_prerequisites is not None:
        _step_flag = {
            "gauges": "gauges", "properties": "properties",
            "mortgages": "mortgages", "gaugehd": "gaugehd",
            "stressm": "stressm", "hazard": "hazard",
            "propertyts": "propertyts", "propertyhc": "propertyhc",
            "propertytsd": "propertytsd", "propertytse": "propertytse",
            "propertyshd": "propertyshd", "propertyshe": "propertyshe",
            "counterparties": "counterparties", "blotter": "blotter",
        }
        requested = [
            name for name, attr in _step_flag.items()
            if getattr(args, attr, False)
                or (name == "stressm" and getattr(args, "gaugets", False))
        ]
        if requested:
            try:
                prereqs = resolve_prerequisites(requested, data_dir=output_dir)
                if prereqs:
                    arrow = ' \u2192 '
                    print(f"  Auto-running prerequisites: "
                          f"{arrow.join(prereqs)}\n")
                    for step in prereqs:
                        setattr(args, _step_flag[step], True)
            except Exception as e:
                print(f"  [lineage] Prerequisite check: {e}")

    if run_all or args.gauges:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("gauges")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'gauges':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("1. Generating Gauges...")
        t_step = time.time()
        r = gauge.GaugePortfolioGenerator(output_dir, verbose=args.verbose).generate(args.num_gauges)
        elapsed_step = time.time() - t_step
        n = len(r['data']['flood_gauges'])
        stats = r.get('processing_stats', {})
        ok = stats.get('successful_gauges', n)
        print(f"   {n} gauges generated  ({ok}/{stats.get('total_gauges', n)} successful)"
              f"  →  gauge.json")
        if record_step is not None:
            try:
                record_step(
                    step_name="gauges",
                    generator="port.src.gauge.GaugePortfolioGenerator",
                    inputs={},
                    outputs={"gauge.json": input_dir / "gauge.json"},
                    parameters={"num_gauges": args.num_gauges},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                )
                stale = get_stale_downstream("gauges")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.properties:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("properties")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'properties':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("2. Generating Properties...")
        _prop_inputs = {"gauge.json": input_dir / "gauge.json"}
        _prop_pre = pre_hash_inputs(_prop_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = prop_gen.PropertyPortfolioGenerator(output_dir).generate(args.num_properties)
        elapsed_step = time.time() - t_step
        n = len(r['data']['properties'])
        stats = r.get('processing_stats', {})
        ok = stats.get('successful_properties', n)
        print(f"   {n} properties generated  ({ok}/{stats.get('total_properties', n)} successful)"
              f"  →  property.json")
        if record_step is not None:
            try:
                record_step(
                    step_name="properties",
                    generator="port.src.property.PropertyPortfolioGenerator",
                    inputs=_prop_inputs,
                    outputs={"property.json": input_dir / "property.json"},
                    parameters={"num_properties": args.num_properties},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_prop_pre,
                )
                stale = get_stale_downstream("properties")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    # 2.5 Synthetic Gauges — create virtual gauges on the river centreline
    # for each property, so stressm/gaugehc process them as real gauges.
    if run_all or args.gauges or args.properties:
        from port.src.gauge.synthetic import SyntheticGaugeGenerator
        print("2.5 Generating Synthetic Gauges...")
        _sg_inputs = {
            "gauge.json": input_dir / "gauge.json",
            "property.json": input_dir / "property.json",
        }
        _sg_pre = pre_hash_inputs(_sg_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = SyntheticGaugeGenerator(output_dir).generate()
        elapsed_step = time.time() - t_step
        n = r.get("count", 0)
        print(f"   {n} synthetic gauges  →  gauge.json (updated)")
        if record_step is not None:
            try:
                record_step(
                    step_name="synthetic_gauges",
                    generator="port.src.gauge.synthetic.SyntheticGaugeGenerator",
                    inputs=_sg_inputs,
                    outputs={"gauge.json": input_dir / "gauge.json"},
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_sg_pre,
                )
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.mortgages:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("mortgages")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'mortgages':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("3. Generating Mortgages...")
        _mtg_inputs = {"property.json": input_dir / "property.json"}
        _mtg_pre = pre_hash_inputs(_mtg_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = mortgage.MortgagePortfolioGenerator(output_dir).generate()
        elapsed_step = time.time() - t_step
        n = len(r['data']['mortgages'])
        stats = r.get('processing_stats', {})
        ok = stats.get('successful_mortgages', n)
        print(f"   {n} mortgages generated  ({ok}/{stats.get('total_mortgages', n)} successful)"
              f"  →  mortgage.json")
        if record_step is not None:
            try:
                record_step(
                    step_name="mortgages",
                    generator="port.src.mortgage.MortgagePortfolioGenerator",
                    inputs=_mtg_inputs,
                    outputs={"mortgage.json": input_dir / "mortgage.json"},
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_mtg_pre,
                )
                stale = get_stale_downstream("mortgages")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.gaugehd:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("gaugehd")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'gaugehd':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("4. Generating Gauge Historical Data...")
        _ghd_inputs = {"gauge.json": input_dir / "gauge.json"}
        _ghd_pre = pre_hash_inputs(_ghd_inputs) if pre_hash_inputs else None
        t_step = time.time()
        files = gaugehd.generate_all_gauge_histories(years=args.history_years)
        elapsed_step = time.time() - t_step
        n = len(files) if files else 0
        print(f"   {n} gauge histories  ×  {args.history_years} years  →  gaugehd/")
        if record_step is not None:
            try:
                record_step(
                    step_name="gaugehd",
                    generator="port.src.gauge.gaugehd",
                    inputs=_ghd_inputs,
                    outputs={"gaugehd/": input_dir / "gaugehd"},
                    parameters={"history_years": args.history_years},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_ghd_pre,
                )
                stale = get_stale_downstream("gaugehd")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    # --gaugets is now handled by stressm (generates base sim + storm responses)
    # gaugehd must run first so stressm can use historical baselines
    if (run_all and not args.nostress) or args.stressm or args.gaugets:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("stressm")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'stressm':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("5. Multi-Storm Sequences + Gaugets + Stress Storms...")
        from port.src.stressm import generate_stressm, GAUGE_SUMMARY_FILENAME
        from port.src.storm_multi.utils.serialization import SEQUENCES_FILENAME, SUMMARY_FILENAME

        # Clean ALL classifiers — they were trained against old storm data
        # and must be retrained per-gauge via the UI after a fresh port run.
        from pathlib import Path as _Path
        _clean_dirs = [
            _Path(config.get_classifiers_dir()),
            _Path(config.get_output_dir()) / "stressm",
            output_dir / "stressm" if output_dir else None,
        ]
        for _cls_dir in _clean_dirs:
            if _cls_dir is None or not _cls_dir.exists():
                continue
            _stale_joblibs = list(_cls_dir.glob("*.joblib"))
            if _stale_joblibs:
                print(f"  Cleaning {len(_stale_joblibs)} stale classifier(s) from {_cls_dir.name}/...")
                for jf in _stale_joblibs:
                    jf.unlink()
            _summary_path = _cls_dir / "training_summary.json"
            if _summary_path.exists():
                _summary_path.unlink()
                print(f"  Removed training_summary.json from {_cls_dir.name}/")

        _sm_inputs = {"gauge.json": input_dir / "gauge.json", "gaugehd/": input_dir / "gaugehd"}
        _sm_pre = pre_hash_inputs(_sm_inputs) if pre_hash_inputs else None
        t_step = time.time()
        summary = generate_stressm(
            input_dir=output_dir,
            output_dir=config.get_output_dir(),
            count=args.num_storms,
            catchment_id=catchment,
            seed=42,
            verbose=args.verbose,
            gauge_id=args.gauge_id,
            train_classifier=False,
        )
        elapsed_step = time.time() - t_step

        tc = summary.get("type_counts", {})
        tc_str = "  ".join(f"{k}: {v:,}" for k, v in sorted(tc.items()))
        n = summary["num_sequences"]
        ng = summary["num_gauges"]
        elapsed = summary.get("elapsed_seconds", 0)

        print(f'\n{"=" * 60}')
        print(f' Multi-Storm Stress Summary')
        print(f'{"=" * 60}')
        print(f' Sequences generated : {n:,}')
        print(f' Types               : {tc_str}')
        print(f' Gauges              : {ng}')
        print(f' Alert sequences     : {summary["alert_sequences"]:,}')
        print(f' Warning sequences   : {summary["warning_sequences"]:,}')
        print(f' Severe sequences    : {summary["severe_sequences"]:,}')
        print(f' Elapsed             : {elapsed:.0f}s ({elapsed / 60:.1f} min)')
        print(f'{"=" * 60}')
        print(f'   Output files:')
        print(f'   gaugets/ (base simulation + storm responses)')
        print(f'   stress_storms/ (per-storm files)')
        print(f'   {SEQUENCES_FILENAME}')
        print(f'   {SUMMARY_FILENAME}')
        print(f'   {GAUGE_SUMMARY_FILENAME}')
        if record_step is not None:
            try:
                record_step(
                    step_name="stressm",
                    generator="port.src.stressm.generate_stressm",
                    inputs=_sm_inputs,
                    outputs={
                        "gaugets/": input_dir / "gaugets",
                        "stress_storms/": input_dir / "stress_storms",
                        "storm_sequences.json": input_dir / "storm_sequences.json",
                        "sequence_gauge/": input_dir / "sequence_gauge",
                    },
                    parameters={"num_storms": args.num_storms},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_sm_pre,
                )
                stale = get_stale_downstream("stressm")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.hazard:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("hazard")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'hazard':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("6. Building Hazard Curves...")
        _hz_inputs = {"gauge.json": input_dir / "gauge.json", "gaugets/": input_dir / "gaugets"}
        _hz_pre = pre_hash_inputs(_hz_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = hazard.build_hazard_curves(
            output_dir=output_dir, catchment_id=catchment,
            distribution=args.distribution, verbose=args.verbose
        )
        elapsed_step = time.time() - t_step
        s = r.get('summary', {})
        n_g = s.get('num_gauges', '?')
        n_s = s.get('num_storms', '?')
        p_alert   = s.get('avg_annual_prob_alert', 0) * 100
        p_warning = s.get('avg_annual_prob_warning', 0) * 100
        p_severe  = s.get('avg_annual_prob_severe', 0) * 100
        print(f"   {n_g} gauge curves  ({n_s:,} individual storms  |  dist: {args.distribution.upper()})")
        print(f"   avg annual P(alert): {p_alert:.2f}%  "
              f"P(warning): {p_warning:.2f}%  "
              f"P(severe): {p_severe:.2f}%")
        if record_step is not None:
            try:
                record_step(
                    step_name="hazard",
                    generator="port.src.hazard.build_hazard_curves",
                    inputs=_hz_inputs,
                    outputs={"gaugehc.json": input_dir / "gaugehc.json", "gaugets/": input_dir / "gaugets"},
                    parameters={"distribution": args.distribution},
                    input_hashes=_hz_pre,
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                )
                stale = get_stale_downstream("hazard")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertyts:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("propertyts")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'propertyts':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("7. Generating Property Flood Time Series...")
        _pts_inputs = {
            "property.json": input_dir / "property.json",
            "gauge.json": input_dir / "gauge.json",
            "gaugets/": input_dir / "gaugets",
        }
        _pts_pre = pre_hash_inputs(_pts_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyts.PropertyTimeSeriesGenerator(output_dir, verbose=args.verbose).generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        flooded = r.get('properties_with_floods', '?')
        events  = r.get('total_flood_events', '?')
        max_d   = r.get('max_depth_m', 0)
        max_dr  = r.get('max_damage_ratio', 0)
        print(f"   {total} properties  |  {flooded} with flood events  |  {events:,} total events")
        print(f"   max depth: {max_d:.2f}m  |  max damage ratio: {max_dr:.1%}")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertyts",
                    generator="port.src.property.propertyts.PropertyTimeSeriesGenerator",
                    inputs=_pts_inputs,
                    outputs={"propertyts/": input_dir / "propertyts"},
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_pts_pre,
                )
                stale = get_stale_downstream("propertyts")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertytsd:
        print("7a. Generating Synthetic Distance Timeseries (propertytsd)...")
        _tsd_inputs = {
            "property.json": input_dir / "property.json",
            "gauge.json": input_dir / "gauge.json",
            "gaugets/": input_dir / "gaugets",
        }
        _tsd_pre = pre_hash_inputs(_tsd_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyts.PropertyTimeSeriesGenerator(output_dir, verbose=args.verbose, mode="shd").generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        flooded = r.get('properties_with_floods', '?')
        events  = r.get('total_flood_events', '?')
        print(f"   {total} properties  |  {flooded} with flood events  |  {events:,} total events")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertytsd",
                    generator="port.src.property.propertyts.PropertyTimeSeriesGenerator(mode=shd)",
                    inputs=_tsd_inputs,
                    outputs={"propertytsd/": input_dir / "propertytsd"},
                    parameters={"mode": "shd"},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_tsd_pre,
                )
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertytse:
        print("7b. Generating Synthetic Elevation Timeseries (propertytse)...")
        _tse_inputs = {
            "property.json": input_dir / "property.json",
            "gauge.json": input_dir / "gauge.json",
            "gaugets/": input_dir / "gaugets",
        }
        _tse_pre = pre_hash_inputs(_tse_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyts.PropertyTimeSeriesGenerator(output_dir, verbose=args.verbose, mode="she").generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        flooded = r.get('properties_with_floods', '?')
        events  = r.get('total_flood_events', '?')
        print(f"   {total} properties  |  {flooded} with flood events  |  {events:,} total events")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertytse",
                    generator="port.src.property.propertyts.PropertyTimeSeriesGenerator(mode=she)",
                    inputs=_tse_inputs,
                    outputs={"propertytse/": input_dir / "propertytse"},
                    parameters={"mode": "she"},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_tse_pre,
                )
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertyhc:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("propertyhc")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'propertyhc':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("8. Building Property Hazard Curves + PRS Pricing...")
        _phc_inputs = {
            "propertyts/": input_dir / "propertyts",
            "gaugehc.json": input_dir / "gaugehc.json",
            "gauge.json": input_dir / "gauge.json",
        }
        _phc_pre = pre_hash_inputs(_phc_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyhc.PropertyHazardCurveGenerator(output_dir, verbose=args.verbose).generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        gev    = r.get('properties_with_gev', '?')
        floor  = r.get('properties_with_floor', '?')
        skipped = r.get('properties_skipped', 0)
        avg_bps = r.get('avg_basis_bps', 0)
        avg_tr  = r.get('avg_transmission_rate', 0) * 100
        print(f"   {total} properties  |  {gev} GEV fit  |  {floor} at floor  |  {skipped} skipped")
        print(f"   avg spread: {avg_bps:.1f} bps  |  avg transmission: {avg_tr:.1f}%")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertyhc",
                    generator="port.src.property.propertyhc.PropertyHazardCurveGenerator",
                    inputs=_phc_inputs,
                    input_hashes=_phc_pre,
                    outputs={"propertyhc.json": input_dir / "propertyhc.json"},
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                )
                stale = get_stale_downstream("propertyhc")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertyshd:
        print("8a. Building Synthetic Distance Hazard Curves (propertyshd)...")
        _shd_inputs = {
            "propertytsd/": input_dir / "propertytsd",
            "gaugehc.json": input_dir / "gaugehc.json",
            "gauge.json": input_dir / "gauge.json",
        }
        _shd_pre = pre_hash_inputs(_shd_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyhc.PropertyHazardCurveGenerator(output_dir, verbose=args.verbose, mode="shd").generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        gev    = r.get('properties_with_gev', '?')
        floor  = r.get('properties_with_floor', '?')
        avg_bps = r.get('avg_basis_bps', 0)
        print(f"   {total} properties  |  {gev} GEV fit  |  {floor} at floor")
        print(f"   avg spread: {avg_bps:.1f} bps")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertyshd",
                    generator="port.src.property.propertyhc.PropertyHazardCurveGenerator(mode=shd)",
                    inputs=_shd_inputs,
                    outputs={"propertyshd.json": input_dir / "propertyshd.json"},
                    parameters={"mode": "shd"},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_shd_pre,
                )
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    if run_all or args.propertyshe:
        print("8b. Building Synthetic Elevation Hazard Curves (propertyshe)...")
        _she_inputs = {
            "propertytse/": input_dir / "propertytse",
            "gaugehc.json": input_dir / "gaugehc.json",
            "gauge.json": input_dir / "gauge.json",
        }
        _she_pre = pre_hash_inputs(_she_inputs) if pre_hash_inputs else None
        t_step = time.time()
        r = propertyhc.PropertyHazardCurveGenerator(output_dir, verbose=args.verbose, mode="she").generate()
        elapsed_step = time.time() - t_step
        total  = r.get('total_properties', '?')
        gev    = r.get('properties_with_gev', '?')
        floor  = r.get('properties_with_floor', '?')
        avg_bps = r.get('avg_basis_bps', 0)
        print(f"   {total} properties  |  {gev} GEV fit  |  {floor} at floor")
        print(f"   avg spread: {avg_bps:.1f} bps")
        if record_step is not None:
            try:
                record_step(
                    step_name="propertyshe",
                    generator="port.src.property.propertyhc.PropertyHazardCurveGenerator(mode=she)",
                    inputs=_she_inputs,
                    outputs={"propertyshe.json": input_dir / "propertyshe.json"},
                    parameters={"mode": "she"},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_she_pre,
                )
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()

    # Spread decomposition: requires propertyhc + propertyshd + propertyshe
    if run_all or (args.propertyhc and args.propertyshd and args.propertyshe):
        hc_exists = (output_dir / 'propertyhc.json').exists()
        shd_exists = (output_dir / 'propertyshd.json').exists()
        she_exists = (output_dir / 'propertyshe.json').exists()
        if hc_exists and shd_exists and she_exists:
            print("8c. Attaching Spread Decomposition to propertyhc.json...")
            gen = propertyhc.PropertyHazardCurveGenerator(output_dir, verbose=args.verbose)
            n = gen.attach_spread_decomposition()
            print(f"   {n} properties decomposed")
            print()

    if run_all or args.counterparties:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("counterparties")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'counterparties':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("9. Generating Counterparties...")
        t_step = time.time()
        r = counterparty.CounterpartyPortfolioGenerator(output_dir, verbose=args.verbose).generate()
        elapsed_step = time.time() - t_step
        n = r.get('metadata', {}).get('total_generated', len(r.get('data', [])))
        print(f"   {n} counterparties generated  →  counterparty.json")
        if record_step is not None:
            try:
                record_step(
                    step_name="counterparties",
                    generator="port.src.counterparty.CounterpartyPortfolioGenerator",
                    inputs={},
                    outputs={"counterparty.json": input_dir / "counterparty.json"},
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                )
                stale = get_stale_downstream("counterparties")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()
    
    if run_all or args.blotter:
        if args.strict and check_inputs_fresh is not None:
            try:
                fresh, issues = check_inputs_fresh("blotter")
                if not fresh:
                    print(f"\n  ✗ STRICT MODE: inputs stale for 'blotter':")
                    for issue in issues:
                        print(f"    - {issue}")
                    print(f"  Run upstream steps first, or omit --strict.")
                    return
            except Exception:
                pass
        print("10. Generating Trading Book (Blotter)...")
        from port.src.book import (
            generate_thames_central_book, generate_trade_pdfs, print_book_summary
        )

        blotter_dir = config.get_reports_dir('prs')
        blotter_dir.mkdir(parents=True, exist_ok=True)
        output_dir_trading = config.get_output_dir()

        # Clean existing trades
        existing = list(blotter_dir.glob('PRS-*'))
        if existing:
            for f in existing:
                f.unlink()

        marks_path = config.get_trading_dir() / 'trade_marks.json'
        if marks_path.exists():
            marks_path.unlink()

        # Clear EOD snapshots and market state
        eod_dir = config.get_eod_dir()
        if eod_dir.exists():
            for f in eod_dir.glob('EOD-*'):
                f.unlink()

        market_path = config.get_trading_dir() / 'market_state.json'
        if market_path.exists():
            market_path.unlink()

        _bl_inputs = {
            "gaugehc.json": input_dir / "gaugehc.json",
            "counterparty.json": input_dir / "counterparty.json",
        }
        _bl_pre = pre_hash_inputs(_bl_inputs) if pre_hash_inputs else None
        t_step = time.time()
        trades = generate_thames_central_book(
            gaugehc_path=config.get_input_dir() / 'gaugehc.json',
            counterparty_path=config.get_input_dir() / 'counterparty.json',
            output_dir=blotter_dir,
            catchment_id=catchment,
            seed=42,
        )

        print_book_summary(trades)

        # Initialize trade_marks.json with all trades as Open
        trading_dir = config.get_trading_dir()
        trading_dir.mkdir(parents=True, exist_ok=True)
        import json as _json
        _marks = {}
        for t in trades:
            sid = t.get('PhysicalSwap', {}).get('Header', {}).get('SwapID')
            if sid:
                _marks[sid] = {'trade_status': 'Open'}
        with open(trading_dir / 'trade_marks.json', 'w') as _f:
            _json.dump(_marks, _f, indent=2)

        print("  Generating trade confirmation PDFs...")
        pdfs = generate_trade_pdfs(trades, blotter_dir)
        print(f"  Generated {len(pdfs)} PDFs")

        print("  Generating 3 months of historical EOD data...")
        try:
            from port.src.historical_eod import generate_historical_eod_series
            num_eods = generate_historical_eod_series(
                trades, config.get_trading_dir(), config.get_input_dir(),
                blotter_dir, seed=42,
            )
            print(f"  Generated {num_eods} historical EOD snapshots")
            if num_eods == 0:
                print("  ⚠️  WARNING: 0 EOD snapshots generated — "
                      "check gaugehc.json has all gauge curves")
        except Exception as e:
            print(f"  ⚠️  ERROR generating historical EOD: {e}")
            print("     Run `python app.py port --blotter` to retry after data is complete")
        elapsed_step = time.time() - t_step
        if record_step is not None:
            try:
                record_step(
                    step_name="blotter",
                    generator="port.src.book.generate_thames_central_book",
                    inputs=_bl_inputs,
                    outputs={
                        "prs/": input_dir / "prs",
                        "blotter/eod/": config.get_eod_dir(),
                        "blotter/market_state.json": config.get_trading_dir() / "market_state.json",
                        "blotter/trade_marks.json": config.get_trading_dir() / "trade_marks.json",
                    },
                    parameters={},
                    elapsed_seconds=elapsed_step,
                    run_id=run_id,
                    input_hashes=_bl_pre,
                )
                stale = get_stale_downstream("blotter")
                if stale:
                    print(f"  ⚠ Dependencies require update: {', '.join(stale)}")
            except Exception as e:
                print(f"  [lineage] Warning: {e}")
        print()
    
    if run_all:
        _print_port_summary(output_dir)

    # PDF report
    if args.pdf or run_all:
        try:
            from reports.port import PortReportGenerator
            audit_dir = config.get_output_dir() / 'audit'
            audit_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = audit_dir / f'port_{config.catchment_id}.pdf'
            gen = PortReportGenerator(input_dir=output_dir, output_path=pdf_path)
            result_path = gen.generate()
            print(f"\n  PDF report: {result_path}")
        except Exception as e:
            print(f"\n  PDF report failed: {e}")

    # Data lineage chain validation
    try:
        from lineage.validation import validate_full_chain
        chain = validate_full_chain()
        if not chain["is_consistent"]:
            print(f"\n  ⚠ Data lineage: {len(chain['stale_steps'])} stale step(s)")
            for s in chain["stale_steps"]:
                print(f"    - {s}")
        else:
            print(f"\n  ✓ Data lineage: all steps consistent")
    except Exception:
        pass

    print(f"Complete! Files in: {output_dir}")


def _print_port_summary(output_dir):
    """Print a detailed report of the generated portfolio."""
    import json, statistics
    from pathlib import Path as _Path
    from datetime import datetime

    W = 72  # report width

    def _load(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            return {}

    def _count_key(path, key):
        return len(_load(path).get(key, {}))

    def _count_dir(directory, pattern):
        try:
            return len(list(_Path(directory).glob(pattern)))
        except Exception:
            return 0

    def _heading(title):
        print(f'\n  {title}')
        print(f'  {"-" * (W - 4)}')

    def _row(label, value, indent=4):
        print(f'{" " * indent}{label:<32s} {value}')

    # ---- Load all data sources ----
    gauge_data = _load(output_dir / 'gauge.json')
    gauges = gauge_data.get('flood_gauges', [])
    gauge_count = len(gauges)

    prop_count   = _count_key(output_dir / 'property.json', 'properties')
    mort_count   = _count_key(output_dir / 'mortgage.json', 'mortgages')
    ctpy_count   = _count_key(output_dir / 'counterparty.json', 'counterparties')
    gaugets_ct   = _count_dir(output_dir / 'gaugets', 'GAUGE-*.json')
    gaugehd_ct   = _count_dir(output_dir / 'gaugehd', 'gauge_GAUGE-*.json')
    propertyts_ct = _count_dir(output_dir / 'propertyts', 'PROP-*.json')
    propertytsd_ct = _count_dir(output_dir / 'propertytsd', 'PROP-*.json')
    propertytse_ct = _count_dir(output_dir / 'propertytse', 'PROP-*.json')
    gcurve_count = _count_key(output_dir / 'gaugehc.json', 'hazard_curves')
    pcurve_count = _count_key(output_dir / 'propertyhc.json', 'property_hazard_curves')
    shd_count = _count_key(output_dir / 'propertyshd.json', 'property_hazard_curves')
    she_count = _count_key(output_dir / 'propertyshe.json', 'property_hazard_curves')

    seq_summary = _load(output_dir / 'sequences_summary.json')
    # sequence_gauge: load from split directory or legacy single file
    _sg_index_path = output_dir / 'sequence_gauge' / '_index.json'
    _sg_legacy_path = output_dir / 'sequence_gauge_summary.json'
    if _sg_index_path.exists():
        gauge_summary = _load(_sg_index_path)
    elif _sg_legacy_path.exists():
        gauge_summary = _load(_sg_legacy_path)
    else:
        gauge_summary = {}
    # stress_storms: load index from directory or legacy single file
    _ss_index_path = output_dir / 'stress_storms' / '_index.json'
    _ss_legacy_path = output_dir / 'stress_storms.json'
    if _ss_index_path.exists():
        stress_storms_data = _load(_ss_index_path)
    elif _ss_legacy_path.exists():
        stress_storms_data = _load(_ss_legacy_path)
    else:
        stress_storms_data = {}
    stress_count = len(stress_storms_data.get('storms', []))

    # Tidal classification
    tidal_counts = {}
    for g in gauges:
        fg = g.get('FloodGauge', g)
        ti = (fg.get('SensorDetails', {})
              .get('GaugeInformation', {})
              .get('TidalInfluence', 'Unknown'))
        tidal_counts[ti] = tidal_counts.get(ti, 0) + 1

    # Seasonal baselines from gaugehd
    winter_means, summer_means = [], []
    for f in (output_dir / 'gaugehd').glob('gauge_*_hd.json'):
        try:
            hd = _load(f)
            mm = hd.get('statistics', {}).get('monthly_means', {})
            if mm:
                winter_means.append(
                    statistics.mean([float(mm.get(m, 0)) for m in ['12', '01', '02']]))
                summer_means.append(
                    statistics.mean([float(mm.get(m, 0)) for m in ['06', '07', '08']]))
        except Exception:
            continue

    # Classifier summary
    stressm_dir = output_dir / 'stressm'
    classifier_ct = _count_dir(stressm_dir, '*.joblib')
    ts = _load(stressm_dir / 'training_summary.json') if stressm_dir.exists() else {}

    # Trading book
    from config import config
    prs_dir = config.get_reports_dir('prs')
    trade_ct = _count_dir(prs_dir, 'PRS-*.json') if prs_dir.exists() else 0
    eod_ct = _count_dir(config.get_eod_dir(), 'EOD-*')

    # ---- Print report ----
    now = datetime.now().strftime('%d-%b-%Y %H:%M')

    print(f'\n{"=" * W}')
    print(f'  MKM PORTFOLIO GENERATION REPORT')
    print(f'  {now}')
    print(f'{"=" * W}')

    # Section 1: Gauge Network
    _heading('1. GAUGE NETWORK')
    _row('Gauges generated', f'{gauge_count}')
    _row('Time series (gaugets)', f'{gaugets_ct} files')
    _row('Historical daily (gaugehd)', f'{gaugehd_ct} files')
    if tidal_counts:
        parts = [f'{v} {k.lower()}' for k, v in sorted(tidal_counts.items())]
        _row('Tidal classification', ', '.join(parts))
    if winter_means:
        w_avg = statistics.mean(winter_means)
        s_avg = statistics.mean(summer_means)
        _row('Avg winter baseline (DJF)', f'{w_avg:.3f} m')
        _row('Avg summer baseline (JJA)', f'{s_avg:.3f} m')
        _row('Seasonal range', f'{w_avg - s_avg:.3f} m')

    # Section 2: Storm Sequences
    _heading('2. STORM SEQUENCES')
    seq_count = seq_summary.get('num_sequences', 0)
    _row('Sequences generated', f'{seq_count:,}')
    tc = seq_summary.get('sequence_type_counts', {})
    if tc:
        parts = [f'{k}: {v:,}' for k, v in sorted(tc.items())]
        _row('Sequence types', ', '.join(parts))
    ic = seq_summary.get('intensity_category_counts', {})
    if ic:
        parts = [f'{k}: {v:,}' for k, v in sorted(ic.items())]
        _row('Intensity categories', ', '.join(parts))
    precip = seq_summary.get('precipitation_mm', {})
    if precip:
        _row('Precipitation (mm)',
             f'min {precip["min"]:.0f} / mean {precip["mean"]:.0f} / max {precip["max"]:.0f}')
    dur = seq_summary.get('duration_hours', {})
    if dur:
        _row('Duration (hours)',
             f'min {dur["min"]:.0f} / mean {dur["mean"]:.0f} / max {dur["max"]:.0f}')

    # Section 3: Stress Testing
    _heading('3. STRESS TESTING')
    _row('Alert-breaching sequences', f'{stress_count:,}')
    alert_seq = gauge_summary.get('alert_sequences')
    warning_seq = gauge_summary.get('warning_sequences')
    severe_seq = gauge_summary.get('severe_sequences')
    if alert_seq is not None:
        _row('Warning sequences', f'{warning_seq:,}')
        _row('Severe sequences', f'{severe_seq:,}')
    _row('GBM classifiers trained', f'{classifier_ct}')
    if ts.get('avg_auc_roc'):
        _row('Average AUC-ROC', f'{ts["avg_auc_roc"]:.4f}')

    # Section 4: Hazard Curves
    _heading('4. HAZARD CURVES')
    _row('Gauge hazard curves (GEV)', f'{gcurve_count}')
    _row('Property hazard curves', f'{pcurve_count}')

    # Section 5: Properties & Mortgages
    _heading('5. PROPERTIES & MORTGAGES')
    _row('Properties generated', f'{prop_count}')
    _row('Flood time series', f'{propertyts_ct} files')
    if propertytsd_ct:
        _row('Synthetic distance TS', f'{propertytsd_ct} files')
    if propertytse_ct:
        _row('Synthetic elevation TS', f'{propertytse_ct} files')
    _row('Mortgages linked', f'{mort_count}')
    _row('Counterparties', f'{ctpy_count}')

    # Section 6: Trading Book
    _heading('6. TRADING BOOK')
    _row('PRS trades', f'{trade_ct}')
    _row('Historical EOD snapshots', f'{eod_ct}')

    # Section 7: Output files
    _heading('7. OUTPUT FILES')
    _row('gauge.json', f'{gauge_count} flood gauges')
    _row('property.json', f'{prop_count} properties')
    _row('mortgage.json', f'{mort_count} mortgages')
    _row('counterparty.json', f'{ctpy_count} counterparties')
    _row('storm_sequences.json', f'{seq_count:,} sequences')
    _row('stress_storms/', f'{stress_count:,} alert storms')
    _row('gaugehc.json', f'{gcurve_count} hazard curves')
    _row('propertyhc.json', f'{pcurve_count} property curves')
    if shd_count:
        _row('propertyshd.json', f'{shd_count} synthetic distance curves')
    if she_count:
        _row('propertyshe.json', f'{she_count} synthetic elevation curves')
    _row('gaugets/', f'{gaugets_ct} gauge time series')
    _row('gaugehd/', f'{gaugehd_ct} historical daily')
    _row('propertyts/', f'{propertyts_ct} property flood series')
    if propertytsd_ct:
        _row('propertytsd/', f'{propertytsd_ct} synthetic distance series')
    if propertytse_ct:
        _row('propertytse/', f'{propertytse_ct} synthetic elevation series')
    _row('stressm/', f'{classifier_ct} classifiers')

    # Data size
    try:
        total_bytes = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
        if total_bytes > 1_073_741_824:
            size_str = f'{total_bytes / 1_073_741_824:.2f} GB'
        else:
            size_str = f'{total_bytes / 1_048_576:.1f} MB'
        _row('Total data size', size_str)
    except Exception:
        pass

    print(f'\n{"=" * W}\n')


