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
Config command - Show current configuration.
"""

from config import config


def register_parser(subparsers):
    """Register the 'config' subcommand."""
    sp = subparsers.add_parser("config", help="Show configuration")
    sp.set_defaults(func=cmd_config)


def cmd_config(args):
    """Show current configuration."""
    print("MKM Physical Risk Platform - Configuration")
    print("-" * 50)
    print(f"  Project root:  {config.get_project_root()}")
    print(f"  Catchment:     {config.catchment_id}")
    print(f"  Input dir:     {config.get_input_dir()}")
    print(f"  Output dir:    {config.get_output_dir()}")
    print(f"  Reports dir:   {config.get_reports_dir()}")
    print(f"  Results dir:   {config.get_results_dir()}")
    print(f"  Server:        {config.SERVER_URL}")
    print(f"  Debug:         {config.DEBUG}")
