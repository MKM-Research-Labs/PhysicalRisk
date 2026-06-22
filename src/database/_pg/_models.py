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


class Property(Base):
    """One residential property (a record from ``property.json`` → ``properties[]``).

    The CDM document is deep (~7 sections, 100+ leaves); the identifying/queryable
    fields are promoted, the verbatim document lives in ``cdm``."""

    __tablename__ = "property"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    property_id: Mapped[str] = mapped_column(primary_key=True)  # e.g. 'PROP-001'
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    uprn: Mapped[str | None] = mapped_column(index=True, default=None)
    property_type: Mapped[str | None] = mapped_column(index=True, default=None)
    status: Mapped[str | None] = mapped_column(default=None)
    property_value: Mapped[float | None] = mapped_column(default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    postcode: Mapped[str | None] = mapped_column(index=True, default=None)
    town_city: Mapped[str | None] = mapped_column(default=None)
    local_authority: Mapped[str | None] = mapped_column(default=None)
    area_sqm: Mapped[float | None] = mapped_column(default=None)
    construction_year: Mapped[int | None] = mapped_column(default=None)
    ea_flood_zone: Mapped[str | None] = mapped_column(index=True, default=None)
    overall_flood_risk: Mapped[str | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full property document


class Loan(Base):
    """One residential loan (``loan.json`` → ``loans[]`` → ``RLoan``)."""

    __tablename__ = "loan"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    rloan_id: Mapped[str] = mapped_column(primary_key=True)     # e.g. 'RLOAN-001'
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    property_id: Mapped[str | None] = mapped_column(index=True, default=None)
    uprn: Mapped[str | None] = mapped_column(default=None)
    currency: Mapped[str | None] = mapped_column(default=None)
    original_loan: Mapped[float | None] = mapped_column(default=None)
    original_ltv: Mapped[float | None] = mapped_column(default=None)
    outstanding_balance: Mapped[float | None] = mapped_column(default=None)
    current_ltv: Mapped[float | None] = mapped_column(default=None)
    account_status: Mapped[str | None] = mapped_column(index=True, default=None)
    default_flag: Mapped[bool | None] = mapped_column(default=None)
    arrears_months: Mapped[int | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full RLoan document


class Commercial(Base):
    """One commercial asset (``commercial.json`` → ``commercial_assets[]`` → ``CommercialAsset``)."""

    __tablename__ = "commercial"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    commercial_id: Mapped[str] = mapped_column(primary_key=True)  # CommercialAsset PropertyID
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    uprn: Mapped[str | None] = mapped_column(default=None)
    property_type: Mapped[str | None] = mapped_column(index=True, default=None)
    status: Mapped[str | None] = mapped_column(default=None)
    property_value: Mapped[float | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full CommercialAsset document


class CommercialLoan(Base):
    """One commercial loan (``commercial_loan.json`` → ``commercial_loans[]`` → ``Mortgage``)."""

    __tablename__ = "commercial_loan"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    mortgage_id: Mapped[str] = mapped_column(primary_key=True)  # e.g. 'CLOAN-001'
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    property_id: Mapped[str | None] = mapped_column(index=True, default=None)
    uprn: Mapped[str | None] = mapped_column(default=None)
    borrower_type: Mapped[str | None] = mapped_column(default=None)
    commercial_type: Mapped[str | None] = mapped_column(index=True, default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full Mortgage document


class Counterparty(Base):
    """One counterparty set (``counterparty.json`` → ``counterparties[]`` → ``CounterpartySet``).

    ``catchment_id`` is the partition key from the save context — the record itself
    carries no catchment (counterparties are scoped by the file they live in)."""

    __tablename__ = "counterparty"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    party_id: Mapped[str] = mapped_column(primary_key=True)     # e.g. 'CTPY-BANK-001'
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    party_name: Mapped[str | None] = mapped_column(index=True, default=None)
    party_id_scheme: Mapped[str | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full CounterpartySet document


class GaugeHazardCurve(Base):
    """One gauge's hazard curve (``gaugehc.json`` → ``hazard_curves[gauge_id]``).

    The pricing-relevant scalars (GEV params + annual hazard rates) are promoted;
    the full curve (incl. ``curve_points`` / ``return_period_levels``) stays in ``cdm``."""

    __tablename__ = "gauge_hazard_curve"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    gauge_id: Mapped[str] = mapped_column(primary_key=True)
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    gauge_name: Mapped[str | None] = mapped_column(default=None)
    latitude: Mapped[float | None] = mapped_column(default=None)
    longitude: Mapped[float | None] = mapped_column(default=None)
    gev_location: Mapped[float | None] = mapped_column(default=None)
    gev_scale: Mapped[float | None] = mapped_column(default=None)
    gev_shape: Mapped[float | None] = mapped_column(default=None)
    annual_hazard_rate_alert: Mapped[float | None] = mapped_column(default=None)
    annual_hazard_rate_warning: Mapped[float | None] = mapped_column(default=None)
    annual_hazard_rate_severe: Mapped[float | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full hazard curve


class PrsTrade(Base):
    """One PRS swap (the keyed ``prs_trade`` artifact → ``PhysicalSwap``).

    Traded, not generated — ``port_run_id`` is nullable. Pricing/status fields are
    promoted for the blotter + risk queries; the full swap stays in ``cdm``."""

    __tablename__ = "prs_trade"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    swap_id: Mapped[str] = mapped_column(primary_key=True)     # PhysicalSwap.Header.SwapID
    port_run_id: Mapped[int | None] = mapped_column(ForeignKey("port_run.id"), index=True)

    trade_type: Mapped[str | None] = mapped_column(default=None)
    counterparty: Mapped[str | None] = mapped_column(index=True, default=None)
    party_id: Mapped[str | None] = mapped_column(index=True, default=None)
    trade_status: Mapped[str | None] = mapped_column(index=True, default=None)
    valuation_date: Mapped[str | None] = mapped_column(default=None)
    notional: Mapped[float | None] = mapped_column(default=None)
    currency: Mapped[str | None] = mapped_column(default=None)
    spread_bps: Mapped[float | None] = mapped_column(default=None)
    npv: Mapped[float | None] = mapped_column(default=None)
    trigger_level: Mapped[str | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full PhysicalSwap document


class EodSnapshot(Base):
    """One end-of-day snapshot (the keyed ``eod_snapshot`` artifact, one per date)."""

    __tablename__ = "eod_snapshot"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    eod_date: Mapped[str] = mapped_column(primary_key=True)    # 'YYYY-MM-DD'
    eod_id: Mapped[str | None] = mapped_column(default=None)
    generated_at: Mapped[str | None] = mapped_column(default=None)
    num_open_trades: Mapped[int | None] = mapped_column(default=None)
    total_notional: Mapped[float | None] = mapped_column(default=None)
    total_daily_pnl: Mapped[float | None] = mapped_column(default=None)
    total_running_pnl: Mapped[float | None] = mapped_column(default=None)

    cdm: Mapped[dict] = mapped_column(JSONB)                   # full EOD snapshot


class PortDocument(Base):
    """One whole-document artifact, stored verbatim — the generic DOCUMENT tier.

    Many artifacts are single JSON documents with no per-entity shredding or
    relational-query need: storm sequences/summaries, perils results (fire,
    seismic), trading state (``market_state`` / ``trade_marks`` / history),
    property & commercial hazard curves, classifier training metadata. Rather
    than a bespoke table each, they share this one — keyed by
    ``(catchment, artifact, mode)`` with the verbatim document in ``cdm`` (JSONB)
    so ``load`` round-trips byte-identically. ``mode`` separates the scenario
    variants (e.g. a property hazard curve per flood/shd/she/…); mode-invariant
    documents simply use the default mode."""

    __tablename__ = "port_document"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    artifact: Mapped[str] = mapped_column(primary_key=True)    # e.g. 'market_state'
    mode: Mapped[str] = mapped_column(primary_key=True)        # scenario mode, e.g. 'flood'

    cdm: Mapped[dict] = mapped_column(JSONB)                   # the verbatim document


class PortRecord(Base):
    """One keyed JSON record, stored verbatim — the generic keyed-record tier.

    The per-entity sharded artifacts: property / commercial / gauge timeseries,
    gauge history, stress storms, sequence-gauge sets, typhoon-damage events.
    Each is a directory of one JSON file per key on the file backend; here they
    share one table — keyed by ``(catchment, artifact, mode, key)`` with the
    verbatim record in ``cdm`` (JSONB). Like ``PortDocument`` but with a per-record
    ``key`` (e.g. a property id, a storm id); ``mode`` carries the timeseries
    scenario variant (mode-invariant artifacts use the default mode)."""

    __tablename__ = "port_record"

    catchment_id: Mapped[str] = mapped_column(ForeignKey("catchment.id"), primary_key=True)
    artifact: Mapped[str] = mapped_column(primary_key=True)    # e.g. 'property_timeseries'
    mode: Mapped[str] = mapped_column(primary_key=True)        # scenario mode, e.g. 'flood'
    key: Mapped[str] = mapped_column(primary_key=True)         # record id, e.g. 'PROP-001'

    cdm: Mapped[dict] = mapped_column(JSONB)                   # the verbatim record
