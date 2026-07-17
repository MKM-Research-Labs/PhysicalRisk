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

"""Object-store client (blob tier) — connectivity + bucket lifecycle.

The ``reachable``-false path needs no infrastructure (it points at a dead
endpoint). The bucket-creation test needs a live MinIO and SKIPS otherwise.
"""

import pytest

from database._pg import _objectstore


def test_reachable_false_when_unreachable(monkeypatch):
    # The config exposes connection values as module constants (read once at
    # import, like the DB settings), so patch the constant, not the env var.
    monkeypatch.setattr("config.database.OBJECT_STORE_ENDPOINT", "127.0.0.1:1")  # nothing listens
    _objectstore.reset_client()
    try:
        assert _objectstore.reachable() is False
    finally:
        _objectstore.reset_client()


def _minio_available() -> bool:
    _objectstore.reset_client()
    return _objectstore.reachable()


@pytest.mark.skipif(
    not _minio_available(),
    reason="no live MinIO (run: scripts/minio-native.sh start)",
)
def test_get_client_creates_missing_bucket(monkeypatch):
    """First use of a fresh bucket creates it."""
    test_bucket = "mkm-objstore-coverage-test"
    default_client, _ = _objectstore.get_client()
    if default_client.bucket_exists(test_bucket):           # clean slate
        default_client.remove_bucket(test_bucket)

    monkeypatch.setattr("config.database.OBJECT_STORE_BUCKET", test_bucket)
    _objectstore.reset_client()
    try:
        client, bucket = _objectstore.get_client()          # bucket missing -> make_bucket
        assert bucket == test_bucket
        assert client.bucket_exists(bucket)
        client.remove_bucket(bucket)                         # leave MinIO as found
    finally:
        _objectstore.reset_client()
