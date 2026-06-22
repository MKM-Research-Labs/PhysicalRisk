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

"""MinIO / S3 object-store client for the blob tier (JSON→Postgres WP1.4).

The binary sibling of ``engine.py`` — the one place the object-store SDK lives.
Holds a lazily-built, process-wide client (mirroring ``get_engine``'s caching),
creates the bucket on first use, and exposes thin ``put`` / ``get`` / ``delete``
helpers over raw ``bytes``. All connection values come from ``config.database``
(rule R1); the only callers are this package's ``PostgresRepository`` (rule R6).

The metadata (which keys exist) lives in the relational ``port_blob`` table, so
listing/existence checks are SQL — this module only moves bytes.
"""

from __future__ import annotations

import io

from minio import Minio

from config.database import get_object_store_config

_client: Minio | None = None
_bucket: str | None = None


def get_client() -> tuple[Minio, str]:
    """Return ``(client, bucket)``, building the client and ensuring the bucket
    exists on first call. Cached process-wide until :func:`reset_client`."""
    global _client, _bucket
    if _client is None:
        cfg = get_object_store_config()
        _client = Minio(cfg["endpoint"], access_key=cfg["access_key"],
                        secret_key=cfg["secret_key"], secure=cfg["secure"])
        _bucket = cfg["bucket"]
        if not _client.bucket_exists(_bucket):
            _client.make_bucket(_bucket)
    return _client, _bucket


def reset_client() -> None:
    """Drop the cached client (e.g. after changing the endpoint in a test)."""
    global _client, _bucket
    _client = None
    _bucket = None


def put_bytes(object_key: str, data: bytes) -> None:
    """Store ``data`` at ``object_key`` (overwrites)."""
    client, bucket = get_client()
    client.put_object(bucket, object_key, io.BytesIO(data), length=len(data))


def get_bytes(object_key: str) -> bytes:
    """Fetch the bytes stored at ``object_key``."""
    client, bucket = get_client()
    response = client.get_object(bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_object(object_key: str) -> None:
    """Remove ``object_key`` (no error if already gone)."""
    client, bucket = get_client()
    client.remove_object(bucket, object_key)


def reachable() -> bool:
    """True if the object store answers — the health check the live tests gate on."""
    try:
        client, bucket = get_client()
        client.bucket_exists(bucket)
        return True
    except Exception:
        return False
