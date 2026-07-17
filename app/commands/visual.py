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
Visual command - Interactive visualization generation.
"""

import sys
import webbrowser

from config import config


def register_parser(subparsers):
    """Register the 'visual' subcommand."""
    sp = subparsers.add_parser("visual", help="Generate interactive visualisation")
    sp.add_argument("--no-browser", action="store_true", help="Don't open browser")
    sp.set_defaults(func=cmd_visual)


def cmd_visual(args):
    """Generate and open the interactive visualisation."""
    from database.config_binding import use_configured_backend
    from visual.core.visualizer import TCEventVisualization

    # The visual data loader reads catchment data through the database seam, so
    # bind the configured backend (file | pg) before building the map.
    use_configured_backend()

    viz = TCEventVisualization(
        input_dir=config.get_input_dir(),
        output_dir=config.get_results_dir()
    )
    
    print("Generating Interactive Flood Risk Visualisation")
    print("=" * 60)
    
    viz_path = viz.create_event_map(output_filename="interactive_visualization.html")
    
    if viz_path:
        print(f"\nVisualisation generated: {viz_path}")
        print(f"File size: {viz_path.stat().st_size / 1024:.1f} KB")
        
        if not args.no_browser:
            webbrowser.open(f"file://{viz_path.absolute()}")
            print("Opened in browser")
    else:
        print("Visualisation generation failed")
        sys.exit(1)
