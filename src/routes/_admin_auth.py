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
Top-level re-export of the admin-password decorator.

The decorator itself lives at ``src/routes/trading/_admin_auth.py`` because
it was introduced for the Trading Desk Control tab. As admin-gating spreads
to other blueprints (PRS commit, governance if/when needed, etc.), this
shim provides a blueprint-agnostic import path:

    from routes._admin_auth import require_admin_password

The existing trading-scoped import continues to work unchanged so the
downstream test fixture in ``tests/routes/trading/test_control_routes.py``
that monkeypatches ``routes.trading._admin_auth._admin_file_path`` is
unaffected.
"""

from .trading._admin_auth import (  # noqa: F401
    _admin_file_path,
    require_admin_password,
)
