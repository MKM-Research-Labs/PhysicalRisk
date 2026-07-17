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

"""Postgres backend internals (engine, ORM models, migrations) — JSON→Postgres WP1.

Private subpackage of ``src/database``: the one place SQLAlchemy/Alembic/SQL is
allowed (rule R6, enforced green by the data-access audit). Re-exports only — no
logic here (rule R4)."""

from ._models import (
    Base,
    Catchment,
    Commercial,
    CommercialLoan,
    Counterparty,
    EodSnapshot,
    Gauge,
    GaugeHazardCurve,
    Loan,
    PortBlob,
    PortDocument,
    PortRecord,
    PortRun,
    Property,
    PrsTrade,
)
from ._auth_models import AppUser, AuditLog, Function, Permission
from .engine import get_engine, get_session, reset_engine

__all__ = [
    "Base", "Catchment", "PortRun", "PortDocument", "PortRecord", "PortBlob",
    "Gauge", "Property", "Loan", "Commercial", "CommercialLoan", "Counterparty",
    "GaugeHazardCurve", "PrsTrade", "EodSnapshot",
    "Function", "AppUser", "Permission", "AuditLog",
    "get_engine", "get_session", "reset_engine",
]
