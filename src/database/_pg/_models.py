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

"""SQLAlchemy table models for the Postgres backend (JSON→Postgres WP1).

Private to ``src/database`` — the sanctioned home for all ORM/SQL (rule R6, kept
green by the data-access audit). WP1.1 defines only the ``catchment`` seed table
that every other table will key against; the relational entity/curve/trade/EOD
tables (WP1.2) and JSONB tables (WP1.3) extend this same ``Base.metadata`` so a
single Alembic ``autogenerate`` sees them all.
"""

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base; ``Base.metadata`` is the single target for Alembic."""


class Catchment(Base):
    """One row per catchment (``thames`` / ``halong`` / ``mekong`` / …).

    First-class so every other table can carry a ``catchment_id`` foreign key —
    the single-DB, multi-catchment design (no schema-per-catchment)."""

    __tablename__ = "catchment"

    id: Mapped[str] = mapped_column(primary_key=True)          # e.g. 'thames'
    display_name: Mapped[str | None] = mapped_column(default=None)
    currency: Mapped[str | None] = mapped_column(default=None)  # ISO 4217, e.g. 'GBP'


class PortRun(Base):
    """Provenance for one persisted artifact document (§2.4).

    A portfolio document (e.g. ``gauge.json``) carries top-level ``generation_metadata``
    alongside its record list. That metadata + a stamp land here as one row, and every
    entity row references it via ``port_run_id`` — so a query can trace any record back
    to the run that produced it, and ``load`` can reattach the original metadata to
    reassemble the exact document."""

    __tablename__ = "port_run"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), index=True)
    artifact: Mapped[str]                                      # e.g. 'gauge_portfolio'
    mode: Mapped[str | None] = mapped_column(default=None)     # scenario mode, if any
    generated_at: Mapped[datetime | None] = mapped_column(default=None)
    schema_version: Mapped[str | None] = mapped_column(default=None)
    generation_metadata: Mapped[dict | None] = mapped_column(JSONB, default=None)


class Gauge(Base):
    """One flood gauge (a record from ``gauge.json`` → ``flood_gauges[]``).

    The identifying / queryable fields are promoted to typed, indexed columns; the
    full ``FloodGauge`` CDM document is preserved verbatim in ``cdm`` (JSONB) so a
    ``load`` round-trips byte-identically. More columns can be promoted later without
    a data migration (the value is already in ``cdm``)."""

    __tablename__ = "gauge"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    gauge_id: Mapped[str] = mapped_column(primary_key=True)    # e.g. 'GAUGE-001'
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    gauge_name: Mapped[str | None] = mapped_column(default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    elevation: Mapped[float | None] = mapped_column(default=None)
    flood_alert: Mapped[float | None] = mapped_column(default=None)
    flood_warning: Mapped[float | None] = mapped_column(default=None)
    severe_flood_warning: Mapped[float | None] = mapped_column(default=None)
    nrfa_station_id: Mapped[str | None] = mapped_column(index=True, default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full FloodGauge document
