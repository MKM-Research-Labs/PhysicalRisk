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

"""Object-store client (blob tier) — connectivity + bucket lifecycle.

The ``reachable``-false path needs no infrastructure (it points at a dead
endpoint). The bucket-creation test needs a live MinIO and SKIPS otherwise.
"""

from unittest.mock import MagicMock

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


@pytest.fixture
def fake_minio(monkeypatch):
    """A stand-in client, so the byte-moving paths run without a live MinIO."""
    client = MagicMock()
    client.bucket_exists.return_value = False
    monkeypatch.setattr(_objectstore, "Minio", MagicMock(return_value=client))
    _objectstore.reset_client()
    yield client
    _objectstore.reset_client()


def test_first_use_creates_the_bucket_once(fake_minio):
    _, bucket = _objectstore.get_client()
    _objectstore.get_client()
    fake_minio.make_bucket.assert_called_once_with(bucket)


def test_put_stores_the_payload_length(fake_minio):
    _objectstore.put_bytes("a/b", b"abc")
    assert fake_minio.put_object.call_args.kwargs["length"] == 3


def test_get_returns_the_body_and_releases_the_connection(fake_minio):
    response = fake_minio.get_object.return_value
    response.read.return_value = b"abc"
    assert _objectstore.get_bytes("a/b") == b"abc"
    response.close.assert_called_once()
    response.release_conn.assert_called_once()


def test_delete_removes_the_object(fake_minio):
    _objectstore.delete_object("a/b")
    assert fake_minio.remove_object.call_args.args[1] == "a/b"


def test_reachable_true_when_the_store_answers(fake_minio):
    assert _objectstore.reachable() is True


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
