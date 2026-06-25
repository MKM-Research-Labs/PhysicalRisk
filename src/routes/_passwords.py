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

"""Password hashing for local-account auth (WP5).

Thin wrappers over werkzeug. ``pbkdf2:sha256`` is pinned explicitly so hashing does
not depend on ``hashlib.scrypt`` (absent on some interpreters)."""

from werkzeug.security import check_password_hash, generate_password_hash

_METHOD = "pbkdf2:sha256"


def hash_password(plaintext: str) -> str:
    """Salted one-way hash of a plaintext password."""
    return generate_password_hash(plaintext, method=_METHOD)


def password_matches(plaintext: str, password_hash: str | None) -> bool:
    """True iff ``plaintext`` matches ``password_hash``. A missing/empty hash (user
    has no password set) never matches."""
    if not password_hash:
        return False
    return check_password_hash(password_hash, plaintext)
