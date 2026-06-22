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

"""Tests for config/database.py — the Postgres connection settings (WP1)."""

import importlib

import config.database as dbcfg


def test_default_url_composes_from_parts(monkeypatch):
    monkeypatch.delenv("MKM_DATABASE_URL", raising=False)
    for var in ("MKM_DB_HOST", "MKM_DB_PORT", "MKM_DB_NAME", "MKM_DB_USER", "MKM_DB_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    mod = importlib.reload(dbcfg)
    assert mod.get_database_url() == "postgresql+psycopg2://mkm:mkm@127.0.0.1:5432/physicalrisk"


def test_full_override_wins(monkeypatch):
    monkeypatch.setenv("MKM_DATABASE_URL", "postgresql+psycopg2://u:p@db.example:6543/prod")
    assert dbcfg.get_database_url() == "postgresql+psycopg2://u:p@db.example:6543/prod"


def test_per_part_env_overrides(monkeypatch):
    monkeypatch.delenv("MKM_DATABASE_URL", raising=False)
    monkeypatch.setenv("MKM_DB_HOST", "pg.internal")
    monkeypatch.setenv("MKM_DB_PORT", "6000")
    monkeypatch.setenv("MKM_DB_NAME", "mkmdb")
    monkeypatch.setenv("MKM_DB_USER", "svc")
    monkeypatch.setenv("MKM_DB_PASSWORD", "secret")
    mod = importlib.reload(dbcfg)
    try:
        assert mod.get_database_url() == "postgresql+psycopg2://svc:secret@pg.internal:6000/mkmdb"
    finally:
        importlib.reload(importlib.import_module("config.database"))  # restore defaults
