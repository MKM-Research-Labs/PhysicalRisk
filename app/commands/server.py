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

import os
import sys
from pathlib import Path

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

        # Build the app once here so the database backend is configured for the
        # check below. The server itself is a fresh process (see the exec).
        create_app()

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

        # Hand over to gunicorn rather than app.run().
        #
        # There must be ONE way this application is served. The launchd agent runs
        # gunicorn from gunicorn.conf.py; if this command ran Werkzeug instead, the
        # supervised service and the one a developer starts would be different
        # servers with different defaults -- and the difference would be discovered
        # at the worst moment. It also meant `--debug` exposed the Werkzeug
        # debugger, which is arbitrary code execution to anything that can reach
        # the port.
        #
        # exec rather than spawn: the server replaces this process, so Ctrl-C and
        # every other signal reach gunicorn directly with no wrapper in between.
        #
        # The catchment cannot travel in the `with` block across an exec, so it is
        # passed in the environment -- MKM_CATCHMENT is what config/catch.py reads,
        # which is the same route the agent and a shell both use.
        repo_root = Path(config.get_project_root())
        argv = [
            str(repo_root / ".venv" / "bin" / "gunicorn"),
            "--config", str(repo_root / "gunicorn.conf.py"),
            "--bind", f"{host}:{port}",
        ]
        if debug:
            # Reload on edit and talk more. Deliberately NOT the Werkzeug debugger:
            # the useful half of debug mode without the remote-code-execution half.
            argv += ["--reload", "--log-level", "debug"]
        argv.append("wsgi:app")

        env = dict(os.environ, MKM_CATCHMENT=config.CATCHMENT)
        print(f"Starting {config.CATCHMENT} server on http://{host}:{port} (gunicorn)")
        if debug:
            print("  --debug: auto-reload on, no interactive debugger")
        sys.stdout.flush()
        os.execve(argv[0], argv, env)
