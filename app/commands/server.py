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


def register_parser(subparsers):
    """Register the 'server' subcommand."""
    sp = subparsers.add_parser("server", help="Start the Flask web server")
    sp.add_argument("--host", type=str, help="Host to bind to")
    sp.add_argument("--port", type=int, help="Port to listen on")
    sp.add_argument("--debug", action="store_true", help="Enable debug mode")
    sp.set_defaults(func=cmd_server)


def cmd_server(args):
    """Start the Flask web server."""
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
        print("     Run:  python app.py port --blotter")
        print("     to generate the Thames Central trading book.")
        print()

    app = create_app()

    print(f"Starting server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
