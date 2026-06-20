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

"""Trading-book stages: counterparties (9), blotter + EOD (10)."""

import json as _json
import time

from config import config

from ..context import StageContext


def run_counterparties(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.counterparties):
        return
    if ctx.strict_block("counterparties"):
        raise SystemExit
    print("9. Generating Counterparties...")
    t_step = time.time()
    r = ctx.counterparty.CounterpartyPortfolioGenerator(verbose=args.verbose).generate()
    elapsed = time.time() - t_step
    n = r.get('metadata', {}).get('total_generated', len(r.get('data', [])))
    print(f"   {n} counterparties generated  →  counterparty.json")
    ctx.record(
        step_name="counterparties",
        generator="port.src.counterparty.CounterpartyPortfolioGenerator",
        inputs={},
        outputs={"counterparty.json": ctx.input_dir / "counterparty.json"},
        parameters={},
        elapsed_seconds=elapsed,
        stale_name="counterparties",
    )
    print()


def run_blotter(ctx: StageContext):
    args = ctx.args
    if not (ctx.run_all or args.blotter):
        return
    if ctx.strict_block("blotter"):
        raise SystemExit
    print("10. Generating Trading Book (Blotter)...")
    from port.src.book import (
        generate_thames_central_book, generate_market_making_book,
        generate_property_book, generate_trade_pdfs, print_book_summary,
    )

    blotter_dir = config.get_reports_dir('prs')
    blotter_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing trades
    for f in list(blotter_dir.glob('PRS-*')):
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

    inputs = {
        "gaugehc.json": ctx.input_dir / "gaugehc.json",
        "counterparty.json": ctx.input_dir / "counterparty.json",
    }
    pre = ctx.hash_inputs(inputs)
    t_step = time.time()
    if ctx.catchment == 'thames':
        # Thames uses a curated 50-trade book hard-mapped to inner-London
        # gauges (Westminster, Lambeth, Southwark, etc.).
        trades = generate_thames_central_book(
            gaugehc_path=config.get_input_dir() / 'gaugehc.json',
            counterparty_path=config.get_input_dir() / 'counterparty.json',
            output_dir=blotter_dir,
            catchment_id=ctx.catchment,
            seed=42,
        )
        _book_generator_name = "port.src.book.generate_thames_central_book"
    else:
        # Other catchments use the algorithmic market-making book, which
        # picks gauges from gaugehc.json without any hardcoded area names.
        trades = generate_market_making_book(
            gaugehc_path=config.get_input_dir() / 'gaugehc.json',
            counterparty_path=config.get_input_dir() / 'counterparty.json',
            output_dir=blotter_dir,
            num_gauges=12,
            catchment_id=ctx.catchment,
            seed=42,
        )
        _book_generator_name = "port.src.book.generate_market_making_book"

    # Property PRS client trades
    prop_trades = generate_property_book(
        propertyhc_path=config.get_input_dir() / 'propertyhc.json',
        property_path=config.get_input_dir() / 'property.json',
        counterparty_path=config.get_input_dir() / 'counterparty.json',
        output_dir=blotter_dir,
        catchment_id=ctx.catchment,
        seed=43,
        propertybri_path=config.get_input_dir() / 'propertybri.json',
    )
    trades.extend(prop_trades)
    if prop_trades:
        print(f"  + {len(prop_trades)} property PRS client trades")

    print_book_summary(trades)

    # Initialise trade_marks.json with all trades as Open
    trading_dir = config.get_trading_dir()
    trading_dir.mkdir(parents=True, exist_ok=True)
    marks = {}
    for t in trades:
        sid = t.get('PhysicalSwap', {}).get('Header', {}).get('SwapID')
        if sid:
            marks[sid] = {'trade_status': 'Open'}
    with open(trading_dir / 'trade_marks.json', 'w') as f:
        _json.dump(marks, f, indent=2)

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
    elapsed = time.time() - t_step
    ctx.record(
        step_name="blotter",
        generator=_book_generator_name,
        inputs=inputs,
        outputs={
            "prs/": ctx.input_dir / "prs",
            "blotter/eod/": config.get_eod_dir(),
            "blotter/market_state.json": config.get_trading_dir() / "market_state.json",
            "blotter/trade_marks.json": config.get_trading_dir() / "trade_marks.json",
        },
        parameters={},
        elapsed_seconds=elapsed,
        input_hashes=pre,
        stale_name="blotter",
    )
    print()


def run_all(ctx: StageContext):
    run_counterparties(ctx)
    run_blotter(ctx)
