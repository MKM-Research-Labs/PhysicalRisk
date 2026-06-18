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

"""CLI entry point for PRS pricing."""

import argparse
import logging

from .io import load_hazard_curves, print_pricing_results
from .pricer import price_prs

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Price Physical Risk Swap using hazard curves")
    parser.add_argument('--hazard-file', '-f', type=str,
                        default='input/thames/gaugehc.json',
                        help='Path to hazard curves JSON file')
    parser.add_argument('--gauge', '-g', type=str, default=None,
                        help='Gauge ID (e.g., THAMES-G001)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available gauges and exit')
    parser.add_argument('--trigger', '-t', type=str,
                        choices=['alert', 'warning', 'severe'],
                        default='warning',
                        help='Trigger level (default: warning)')
    parser.add_argument('--notional', '-n', type=float, default=10_000_000,
                        help='Notional amount (default: 10M)')
    parser.add_argument('--tenor', type=int, default=5,
                        help='Contract tenor in years (default: 5)')
    parser.add_argument('--spread', '-s', type=float, default=0.01,
                        help='Running spread (default: 0.01 = 100bps)')
    parser.add_argument('--flat', action='store_true',
                        help='Use flat hazard rate instead of term structure')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Load hazard curves
    logger.info(f"Loading hazard curves from {args.hazard_file}...")
    data = load_hazard_curves(args.hazard_file)

    # Handle --list
    if args.list:
        logger.info(f"Available Gauges ({len(data['hazard_curves'])} total):")
        for gauge_id, gauge_data in data['hazard_curves'].items():
            logger.info(f"  {gauge_id}: {gauge_data['gauge_name']}")
        return 0

    # Select gauge
    if args.gauge:
        if args.gauge not in data['hazard_curves']:
            logger.error(f"Gauge '{args.gauge}' not found")
            logger.info("Available gauges:")
            for gid in list(data['hazard_curves'].keys())[:10]:
                logger.info(f"  {gid}")
            if len(data['hazard_curves']) > 10:
                logger.info(f"  ... and {len(data['hazard_curves']) - 10} more (use --list to see all)")
            return 1
        gauge_data = data['hazard_curves'][args.gauge]
    else:
        # Use first gauge
        gauge_data = list(data['hazard_curves'].values())[0]
        logger.info(f"No gauge specified, using {gauge_data['gauge_id']}")

    # Price PRS
    results = price_prs(
        gauge_data=gauge_data,
        trigger_level=args.trigger,
        notional=args.notional,
        tenor_years=args.tenor,
        running_spread=args.spread,
        use_term_structure=not args.flat
    )

    # Print results
    print_pricing_results(results)

    return 0


if __name__ == "__main__":
    exit(main())
