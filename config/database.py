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

"""PostgreSQL connection settings for the JSON→Postgres backend (WP1).

This module holds the connection *values* only (rule R1 — every parameter lives
in the ``config`` package). It deliberately imports no SQL driver: the engine,
sessions, and all ORM/SQL live in ``src/database`` (rule R6, kept green by the
data-access audit). The defaults match ``docker/docker-compose.yml`` so a local
``docker compose up`` + the app point at the same database out of the box.
"""

import os

# Per-part defaults (overridden individually, or wholesale via MKM_DATABASE_URL).
DB_HOST = os.getenv("MKM_DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("MKM_DB_PORT", "5432")
DB_NAME = os.getenv("MKM_DB_NAME", "physicalrisk")
DB_USER = os.getenv("MKM_DB_USER", "mkm")
DB_PASSWORD = os.getenv("MKM_DB_PASSWORD", "mkm")

# SQLAlchemy dialect+driver. psycopg2 is the installed driver (requirements.txt).
DB_DRIVER = "postgresql+psycopg2"


def get_database_url() -> str:
    """The SQLAlchemy URL for the Postgres backend.

    Honours a full ``MKM_DATABASE_URL`` override; otherwise composes one from the
    per-part settings above. Used by ``src/database`` to build the engine and by
    Alembic to run migrations against the same target.
    """
    override = os.getenv("MKM_DATABASE_URL")
    if override:
        return override
    return f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ── Object store (blob tier) ────────────────────────────────────────────────
# Connection values for the MinIO/S3 object store that holds binary artifacts
# (classifiers, typhoon particle files). Values only — the client lives in
# ``src/database`` (rule R6). Defaults match docker/docker-compose.yml's minio.
OBJECT_STORE_ENDPOINT = os.getenv("MKM_OBJECT_STORE_ENDPOINT", "127.0.0.1:9000")
OBJECT_STORE_ACCESS_KEY = os.getenv("MKM_OBJECT_STORE_ACCESS_KEY", "minioadmin")
OBJECT_STORE_SECRET_KEY = os.getenv("MKM_OBJECT_STORE_SECRET_KEY", "minioadmin")
OBJECT_STORE_BUCKET = os.getenv("MKM_OBJECT_STORE_BUCKET", "mkm-physicalrisk")
# TLS off for local MinIO; set MKM_OBJECT_STORE_SECURE=1 for an https endpoint.
OBJECT_STORE_SECURE = os.getenv("MKM_OBJECT_STORE_SECURE", "0").strip().lower() in ("1", "true", "yes")


def get_object_store_config() -> dict:
    """Connection settings for the blob-tier object store, as a plain dict
    (``endpoint`` / ``access_key`` / ``secret_key`` / ``bucket`` / ``secure``).
    Consumed by ``src/database`` to build the MinIO client."""
    return {
        "endpoint": OBJECT_STORE_ENDPOINT,
        "access_key": OBJECT_STORE_ACCESS_KEY,
        "secret_key": OBJECT_STORE_SECRET_KEY,
        "bucket": OBJECT_STORE_BUCKET,
        "secure": OBJECT_STORE_SECURE,
    }


# Backend selection (WP2.1 cutover switch). 'file' = the JSON tree (default,
# unchanged behaviour); 'pg' = the PostgreSQL backend.
REPO_BACKENDS = ("file", "pg")


def get_repo_backend() -> str:
    """Which repository backend to bind at startup, from ``MKM_REPO_BACKEND``
    ('file' by default, or 'pg'). Raises ``ValueError`` for anything else."""
    backend = os.getenv("MKM_REPO_BACKEND", "file").strip().lower()
    if backend not in REPO_BACKENDS:
        raise ValueError(
            f"MKM_REPO_BACKEND must be one of {REPO_BACKENDS}, got '{backend}'"
        )
    return backend


# ── Dev-service start hints ─────────────────────────────────────────────────
# Shown by the test preflight when a service is down. The dev services run
# natively (Homebrew) with their data dirs on the external SSD; these are the
# commands that start them.
POSTGRES_START_HINT = "scripts/pg-native.sh start"
MINIO_START_HINT = "scripts/minio-native.sh start"

# Set to '1' to run the unit suite with Postgres down. The coverage gate cannot
# pass in that state — the escape hatch exists for deliberate partial runs.
NO_SERVICE_OVERRIDE_ENV = "MKM_ALLOW_NO_POSTGRES"
