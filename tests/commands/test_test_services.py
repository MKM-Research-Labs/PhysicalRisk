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

"""The unit-suite live-service preflight (app.commands.test.services).

Service reachability is stubbed throughout, so these assert the preflight's
decisions rather than whether Postgres happens to be up on this machine.
"""

import pytest

import database
from app.commands.test import services

from config.database import (
    MINIO_START_HINT,
    NO_SERVICE_OVERRIDE_ENV,
    POSTGRES_START_HINT,
)


@pytest.fixture
def _services(monkeypatch):
    """Stub both reachability probes; returns a setter taking (pg, minio)."""
    def _set(pg: bool, minio: bool):
        monkeypatch.setattr(services, '_postgres_reachable', lambda: pg)
        monkeypatch.setattr(services, '_minio_reachable', lambda: minio)
    return _set


def test_skipped_entirely_when_no_unit_suite(_services, capsys):
    """--lineage/--audit alone must not probe or block: no unit suite, no gate."""
    _services(pg=False, minio=False)
    assert services.check_live_services(do_unit=False) == 0
    assert capsys.readouterr().out == ''


def test_proceeds_silently_when_both_services_up(_services, capsys):
    _services(pg=True, minio=True)
    assert services.check_live_services(do_unit=True) == 0
    assert capsys.readouterr().out == ''


def test_aborts_when_postgres_down(_services, capsys):
    _services(pg=False, minio=True)
    assert services.check_live_services(do_unit=True) == 1
    out = capsys.readouterr().out
    assert 'POSTGRES IS NOT REACHABLE' in out
    assert POSTGRES_START_HINT in out          # tells you how to fix it
    assert NO_SERVICE_OVERRIDE_ENV in out      # ...and how to bypass it


def test_postgres_down_message_explains_the_coverage_symptom(_services, capsys):
    """The whole point: name the coverage symptom so a service outage is not
    misread as a test gap."""
    _services(pg=False, minio=True)
    services.check_live_services(do_unit=True)
    out = capsys.readouterr().out
    assert 'coverage' in out.lower()


def test_override_continues_despite_postgres_down(_services, monkeypatch, capsys):
    monkeypatch.setenv(NO_SERVICE_OVERRIDE_ENV, '1')
    _services(pg=False, minio=True)
    assert services.check_live_services(do_unit=True) == 0
    assert 'continuing without Postgres' in capsys.readouterr().out


def test_override_only_honours_exactly_one(_services, monkeypatch):
    """A stray truthy value must not silently disable the gate."""
    monkeypatch.setenv(NO_SERVICE_OVERRIDE_ENV, 'yes')
    _services(pg=False, minio=True)
    assert services.check_live_services(do_unit=True) == 1


def test_minio_down_warns_but_does_not_abort(_services, capsys):
    """MinIO carries no coverage gate — warn, never block."""
    _services(pg=True, minio=False)
    assert services.check_live_services(do_unit=True) == 0
    out = capsys.readouterr().out
    assert 'MinIO is not reachable' in out
    assert MINIO_START_HINT in out


def test_both_down_reports_both(_services, capsys):
    _services(pg=False, minio=False)
    assert services.check_live_services(do_unit=True) == 1
    out = capsys.readouterr().out
    assert 'MinIO is not reachable' in out
    assert 'POSTGRES IS NOT REACHABLE' in out


def test_probes_never_raise_when_backend_unreachable(monkeypatch):
    """Both probes swallow any failure — a broken driver must not crash the run
    before the diagnostic banner prints."""
    def _boom(*a, **k):
        raise RuntimeError('driver exploded')

    monkeypatch.setattr(database, 'postgres_reachable', _boom)
    monkeypatch.setattr(database, 'object_store_reachable', _boom)
    assert services._postgres_reachable() is False
    assert services._minio_reachable() is False


def test_probes_delegate_to_the_database_public_api(monkeypatch):
    """The probes must go through the seam, not their own connection."""
    monkeypatch.setattr(database, 'postgres_reachable', lambda: True)
    monkeypatch.setattr(database, 'object_store_reachable', lambda: False)
    assert services._postgres_reachable() is True
    assert services._minio_reachable() is False
