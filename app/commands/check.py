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
Check command - Dependency validation and documentation generation.
"""

import sys
import subprocess as sp


def register_parser(subparsers):
    """Register the 'check' subcommand."""
    sp_check = subparsers.add_parser("check", help="Check dependencies or generate test docs")
    sp_check.set_defaults(func=cmd_check)
    
    check_sub = sp_check.add_subparsers(dest="check_sub")
    
    # check tests
    sp_tests = check_sub.add_parser("tests", help="Run tests and generate LaTeX documentation")
    sp_tests.add_argument("--pdf", action="store_true", help="Compile LaTeX to PDF")
    sp_tests.add_argument("--model", nargs="+", help="Filter by model alias")
    
    # check params
    sp_params = check_sub.add_parser("params", help="Generate parameter inventory")
    sp_params.add_argument("--pdf", action="store_true", help="Compile LaTeX to PDF")


def cmd_check(args):
    """Check dependencies or run test documentation generation."""
    subcommand = getattr(args, 'check_sub', None)
    
    if subcommand == 'tests':
        _cmd_check_tests(args)
    elif subcommand == 'params':
        _cmd_check_params(args)
    else:
        _cmd_check_deps()


def _cmd_check_deps():
    """Check if all required dependencies are installed."""
    required = [
        "flask", "flask_cors", "folium", "pandas", "numpy",
        "geopandas", "reportlab", "scipy", "sklearn",
        "rasterio", "geopy", "shapely", "matplotlib", "seaborn"
    ]
    
    print("Checking Python dependencies...")
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"  ✗ {package}")
    
    if missing:
        print(f"\nMissing packages: {missing}")
        print(f"Install with: pip install {' '.join(missing)}")
        sys.exit(1)
    else:
        print("\n✓ All dependencies satisfied")


def _cmd_check_tests(args):
    """Run model tests and generate LaTeX documentation."""
    cmd = [sys.executable, "-m", "docs.models.test_results.generator"]
    
    if getattr(args, 'pdf', False):
        cmd.append('--pdf')
    
    model_filter = getattr(args, 'model', None)
    if model_filter:
        cmd.extend(['--model'] + model_filter)
    
    result = sp.run(cmd)
    sys.exit(result.returncode)


def _cmd_check_params(args):
    """Generate parameter inventory LaTeX documentation."""
    cmd = [sys.executable, "-m", "docs.models.parameter_inventory.generator"]
    
    if getattr(args, 'pdf', False):
        cmd.append('--pdf')
    
    result = sp.run(cmd)
    sys.exit(result.returncode)
