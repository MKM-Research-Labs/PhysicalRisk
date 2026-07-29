#!/usr/bin/env python3

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

    # Pin the catchment for the lifetime of the server process (the ``with`` block
    # spans ``app.run``); restored on shutdown. Replaces the old permanent
    # ``config.catchment_id = catchment`` mutation.
    with config.use_catchment(catchment):
        from server import create_app

        host = args.host or config.SERVER_HOST
        port = args.port or config.SERVER_PORT
        debug = args.debug or config.DEBUG

        app = create_app()

        # Warn if no PRS trades exist — blotter will be empty until generated.
        # Done after create_app(), which configures the database backend.
        import database
        prs_trades = list(database.iter_prs_trade_ids(database.active_catchment()))
        if not prs_trades:
            print()
            print("  ⚠  No PRS trades found for this catchment.")
            print("     The Trading Desk blotter will be empty.")
            print(f"     Run:  python phys.py port --{config.CATCHMENT} --blotter")
            print(f"     to generate the {config.CATCHMENT} trading book.")
            print()

        print(f"Starting {config.CATCHMENT} server on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
