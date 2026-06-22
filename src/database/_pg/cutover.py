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

"""Catchment cutover CLI (JSON→Postgres WP2.2).

The repeatable workflow for moving one catchment onto the Postgres backend:
optionally ETL its files into Postgres + the object store, then run the dual-read
parity harness and exit non-zero on any mismatch. This is the gate WP2 leans on
to flip catchments one at a time, and the runnable form of WP1.7's CI parity job.

    PYTHONPATH=src python -m database._pg.cutover mekong            # verify only
    PYTHONPATH=src python -m database._pg.cutover mekong --import   # import then verify

Repos are injectable so the orchestration is unit-testable without a live DB; the
default ``main`` builds the config-bound file backend and a ``PostgresRepository``.
"""

from __future__ import annotations

import argparse

from ..config_binding import from_config
from .etl import import_catchment
from .parity import all_ok, check_catchment, format_report
from .pg_repo import PostgresRepository


def run_import(catchment, file_repo, pg) -> dict:
    """ETL ``catchment`` from files into Postgres + object store; print a report."""
    counts = import_catchment(catchment, file_repo=file_repo, pg=pg)
    total = sum(counts.values())
    print(f"imported {total} records for '{catchment}' across "
          f"{sum(1 for n in counts.values() if n)} non-empty artifacts")
    return counts


def verify(catchment, file_repo, pg) -> bool:
    """Run the dual-read parity harness for ``catchment``; print the report and
    return whether every check passed."""
    results = check_catchment(catchment, file_repo=file_repo, pg=pg)
    print(format_report(catchment, results))
    return all_ok(results)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="cutover", description="Import and/or dual-read-verify a catchment on Postgres.")
    parser.add_argument("catchment", help="catchment name, e.g. 'mekong'")
    parser.add_argument("--import", dest="do_import", action="store_true",
                        help="ETL the catchment from files into Postgres before verifying")
    return parser.parse_args(argv)


def main(argv=None, *, file_repo=None, pg=None) -> int:
    """Entry point. Returns 0 when parity holds, 1 on any mismatch."""
    args = _parse_args(argv)
    file_repo = file_repo if file_repo is not None else from_config()
    pg = pg if pg is not None else PostgresRepository()
    if args.do_import:
        run_import(args.catchment, file_repo, pg)
    return 0 if verify(args.catchment, file_repo, pg) else 1


if __name__ == "__main__":           # pragma: no cover - module entry point
    raise SystemExit(main())
