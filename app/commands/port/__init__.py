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

"""Port command package — generates synthetic portfolio data.

Public surface (preserved for back-compat with the old port.py module):

    register_parser(subparsers)   — argparse plumbing
    cmd_port(args)                — top-level orchestrator
    _authenticate                 — admin gate (used by tests)
    _set_password                 — first-time password creation
    _verify_password              — env-var / prompt verification
    _ADMIN_FILE                   — Path to the .port_admin hash file
    _print_port_summary           — end-of-run report (used by tests)
"""

from .auth import _ADMIN_FILE, _authenticate, _set_password, _verify_password
from .orchestrator import cmd_port
from .parser import register_parser
from .summary import _print_port_summary

__all__ = [
    "register_parser",
    "cmd_port",
    "_authenticate",
    "_set_password",
    "_verify_password",
    "_ADMIN_FILE",
    "_print_port_summary",
]
