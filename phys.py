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
MKM Research Labs - Physical Risk Platform

Unified CLI for all platform operations.

Usage:
    python3 phys.py server                # Start Flask web server
    python3 phys.py server --port 8080    # Custom port
    python3 phys.py server --debug        # Debug mode
    
    python3 phys.py port                  # Generate all synthetic data
    python3 phys.py port --gauges         # Only gauges
    python3 phys.py port --properties --mortgages  # Multiple segments
    python3 phys.py port --num-properties 500      # Custom counts
    
    python3 phys.py visual                # Generate & open visualisation
    python3 phys.py visual --no-browser   # Generate only
    
    python3 phys.py check                 # Check dependencies
    python3 phys.py config                # Show configuration
    
    python3 phys.py test --audit          # Full audit evidence package
    python3 phys.py test --test           # Run pytest only (skip doc generators)
    python3 phys.py test --code           # Run doc generators only (skip pytest)
    python3 phys.py test --audit --pdf    # Also compile LaTeX to PDF
    python3 phys.py test --audit --model TD GH  # Filtered by model alias
"""

import sys
from app.cli import build_parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Propagate the command's return code. Handlers that return None (the
    # common "nothing went wrong" case) exit 0; an int return becomes the
    # process exit status, so callers and CI can detect failure.
    rc = args.func(args)
    sys.exit(rc if isinstance(rc, int) else 0)


if __name__ == "__main__":
    main()
