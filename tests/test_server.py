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

"""create_app wiring checks."""


def test_create_app_sets_session_secret_key(flask_app):
    """The WP5 login flow signs the session cookie, so a secret key must be set."""
    from config.auth import SECRET_KEY
    assert flask_app.secret_key == SECRET_KEY
    assert flask_app.secret_key  # non-empty -> sessions usable


def test_auth_and_admin_blueprints_registered(flask_app):
    rules = {r.rule for r in flask_app.url_map.iter_rules()}
    assert {"/auth/login", "/auth/logout", "/auth/me"} <= rules
    assert {"/admin", "/admin/api/users", "/admin/api/permissions"} <= rules
