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
MKM Research Labs - Physical Risk Platform

Unified CLI for all platform operations.

Usage:
    python3 app.py server                # Start Flask web server
    python3 app.py server --port 8080    # Custom port
    python3 app.py server --debug        # Debug mode
    
    python3 app.py port                  # Generate all synthetic data
    python3 app.py port --gauges         # Only gauges
    python3 app.py port --properties --mortgages  # Multiple segments
    python3 app.py port --num-properties 500      # Custom counts
    
    python3 app.py visual                # Generate & open visualisation
    python3 app.py visual --no-browser   # Generate only
    
    python3 app.py check                 # Check dependencies
    python3 app.py config                # Show configuration
    
    python3 app.py test --audit          # Full audit evidence package
    python3 app.py test --test           # Run pytest only (skip doc generators)
    python3 app.py test --code           # Run doc generators only (skip pytest)
    python3 app.py test --audit --pdf    # Also compile LaTeX to PDF
    python3 app.py test --audit --model TD GH  # Filtered by model alias
"""

import sys
from app.cli import build_parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
