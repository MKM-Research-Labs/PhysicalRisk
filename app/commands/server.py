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
Server command - Flask web server.
"""

from config import config

from ._catchment import add_catchment_flags, resolve_catchment


def register_parser(subparsers):
    """Register the 'server' subcommand."""
    sp = subparsers.add_parser("server", help="Start the Flask web server")
    add_catchment_flags(sp)
    sp.add_argument("--host", type=str, help="Host to bind to")
    sp.add_argument("--port", type=int, help="Port to listen on")
    sp.add_argument("--debug", action="store_true", help="Enable debug mode")
    sp.set_defaults(func=cmd_server)


def cmd_server(args):
    """Start the Flask web server.

    Catchment selection precedence (highest first):
      1. A per-catchment flag (``--thames`` / ``--halong`` / …) or the
         generic ``--catchment-id``
      2. ``MKM_CATCHMENT`` env var
      3. Interactive prompt (only when (1) and (2) are both absent)

    The chosen catchment is pinned on the global ``config`` singleton so
    every request and lazy import resolves against the same catchment for
    the lifetime of the process.
    """
    catchment = resolve_catchment(args)
    if catchment is None:
        return
    config.catchment_id = catchment

    from server import create_app

    host = args.host or config.SERVER_HOST
    port = args.port or config.SERVER_PORT
    debug = args.debug or config.DEBUG

    # Warn if no PRS trade files exist — blotter will be empty until generated.
    prs_dir = config.get_reports_dir('prs')
    prs_trades = list(prs_dir.glob('PRS-*.json')) if prs_dir.exists() else []
    if not prs_trades:
        print()
        print("  ⚠  No PRS trade files found in:")
        print(f"       {prs_dir}")
        print("     The Trading Desk blotter will be empty.")
        print(f"     Run:  python app.py port --{config.CATCHMENT} --blotter")
        print(f"     to generate the {config.CATCHMENT} trading book.")
        print()

    app = create_app()

    print(f"Starting {config.CATCHMENT} server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
