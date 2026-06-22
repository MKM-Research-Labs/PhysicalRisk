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
Book command - PRS trading book generation.
"""

import logging
from pathlib import Path

from config import config


def register_parser(subparsers):
    """Register the 'book' subcommand."""
    sp = subparsers.add_parser("book", help="Generate market-making book of PRS trades")
    sp.add_argument("--style", choices=["thames-central", "market-making"],
                   default="thames-central",
                   help="Book style: thames-central or market-making")
    sp.add_argument("--num-gauges", "-ng", type=int, default=12,
                   help="Number of gauges for market-making style")
    sp.add_argument("--clean", action="store_true", default=True,
                   help="Delete existing trades first (default: True)")
    sp.add_argument("--no-clean", dest="clean", action="store_false",
                   help="Keep existing trades")
    sp.add_argument("--pdf", action="store_true",
                   help="Generate trade confirmation PDFs")
    sp.add_argument("--seed", type=int, default=42,
                   help="Random seed")
    sp.add_argument("--verbose", "-v", action="store_true")
    sp.set_defaults(func=cmd_book)


def cmd_book(args):
    """Generate a PRS trading book."""
    from port.src.book import (
        generate_market_making_book, generate_thames_central_book,
        generate_trade_pdfs, print_book_summary
    )
    
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
    
    catchment = 'thames'
    # Scope the catchment for the run (replaces permanent ``config.catchment_id =``).
    with config.use_catchment(catchment):
        gaugehc_path = config.get_input_dir() / 'gaugehc.json'
        counterparty_path = config.get_input_dir() / 'counterparty.json'
        output_dir = config.get_reports_dir('prs')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Clean existing trades if requested
        if args.clean:
            existing = list(output_dir.glob('PRS-*'))
            if existing:
                for f in existing:
                    f.unlink()
                print(f"Cleaned {len(existing)} existing trade files")

            marks_path = config.get_trading_dir() / 'trade_marks.json'
            if marks_path.exists():
                marks_path.unlink()
                print("Cleared trade marks")

            eod_dir = config.get_eod_dir()
            if eod_dir.exists():
                eod_files = list(eod_dir.glob('EOD-*'))
                if eod_files:
                    for f in eod_files:
                        f.unlink()
                    print(f"Cleared {len(eod_files)} EOD snapshots")

            market_path = config.get_trading_dir() / 'market_state.json'
            if market_path.exists():
                market_path.unlink()
                print("Cleared market state")

        print(f"\nGenerating {args.style} book")
        print(f"Output: {output_dir}\n")

        if args.style == 'thames-central':
            trades = generate_thames_central_book(
                gaugehc_path=gaugehc_path,
                counterparty_path=counterparty_path,
                output_dir=output_dir,
                catchment_id=catchment,
                seed=args.seed,
            )
        else:
            trades = generate_market_making_book(
                gaugehc_path=gaugehc_path,
                counterparty_path=counterparty_path,
                output_dir=output_dir,
                num_gauges=args.num_gauges,
                catchment_id=catchment,
                seed=args.seed,
            )

        print("Generating trade confirmation PDFs...")
        pdfs = generate_trade_pdfs(trades, output_dir)
        print(f"  Generated {len(pdfs)} PDFs")

        print_book_summary(trades)
