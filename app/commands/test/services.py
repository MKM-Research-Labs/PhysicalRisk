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

"""Live dev-service preflight for the unit suite.

The ``database/_pg`` tests skip when Postgres is unreachable, which silently
removes ~300 covered lines and drops total coverage below the fail_under gate.
The run then reports a coverage miss rather than a missing service, so the
obvious response is to go writing tests that already exist. Checking up front
turns a 17-minute misdiagnosis into an immediate, actionable message.
"""

import os

from config.database import (
    MINIO_START_HINT,
    NO_SERVICE_OVERRIDE_ENV,
    POSTGRES_START_HINT,
)


def _postgres_reachable() -> bool:
    """True when Postgres answers. Probed through the database public API — no
    SQL or driver import lives outside ``src/database`` (rule R6)."""
    try:
        import database

        return bool(database.postgres_reachable())
    except Exception:
        return False


def _minio_reachable() -> bool:
    """True when the blob tier answers; best-effort, never raises."""
    try:
        import database

        return bool(database.object_store_reachable())
    except Exception:
        return False


def check_live_services(do_unit: bool) -> int:
    """Preflight the services the unit suite needs.

    Returns 0 to proceed, or 1 to abort. Postgres is treated as required
    because without it the coverage gate cannot pass; MinIO only warns, since
    its tests are a handful and carry no gate. Set the override env var to
    proceed anyway (a run without Postgres cannot clear the gate).
    """
    if not do_unit:
        return 0

    pg_ok = _postgres_reachable()
    minio_ok = _minio_reachable()

    if not minio_ok:
        print()
        print('  WARNING: MinIO is not reachable — blob-tier tests will skip.')
        print(f'  Start it with: {MINIO_START_HINT}')
        print()

    if pg_ok:
        return 0

    override = os.environ.get(NO_SERVICE_OVERRIDE_ENV) == '1'
    print()
    print('!' * 60)
    print('  POSTGRES IS NOT REACHABLE')
    print('!' * 60)
    print('  The database/_pg tests will skip. That is not a test gap — it')
    print('  removes ~300 covered lines and pushes total coverage ~1 point')
    print('  below the fail_under gate, so the run reports a coverage miss')
    print('  instead of a missing service.')
    print()
    print(f'  Start it with: {POSTGRES_START_HINT}')
    print()
    if not override:
        print(f'  To run anyway (the coverage gate will fail): {NO_SERVICE_OVERRIDE_ENV}=1')
        print('!' * 60)
        print()
        return 1
    print(f'  {NO_SERVICE_OVERRIDE_ENV}=1 set — continuing without Postgres.')
    print('!' * 60)
    print()
    return 0
