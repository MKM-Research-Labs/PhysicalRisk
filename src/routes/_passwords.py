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
