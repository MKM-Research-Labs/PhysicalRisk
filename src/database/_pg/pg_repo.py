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

"""PostgreSQL implementation of the ``Repository`` interface (JSON→Postgres WP1.6).

Backs the document-oriented seam with the relational tables defined under
``src/database/_pg`` in four shapes: a *collection* artifact (e.g. ``gauge`` →
``flood_gauges[]``) is shredded into one entity row per record on save and
reassembled on load; a *keyed* artifact (``prs_trade`` / ``eod_snapshot``) is one
bespoke row per key; a *document* artifact (storm summaries, perils, trading
state, hazard curves, …) is stored whole in one ``PortDocument`` row per
``(catchment, artifact, mode)``; a *keyed-record* artifact (timeseries, stress
storms, sequence gauges, typhoon events) is one ``PortRecord`` row per
``(catchment, artifact, mode, key)``. The JSON shapes keep the verbatim record in
``cdm`` (JSONB), so ``save`` then ``load`` returns an equal document. Finally a
*blob* artifact (classifiers, typhoon particle files) stores its bytes in the
object store with one ``PortBlob`` metadata row per key — proven by the parity
tests.

v1 scope: round-trip fidelity (id + cdm + the document envelope in ``port_run``)
for the 9 tier-1 artifacts. Records reassemble in id order (deterministic, not
source-file order — the consumers key by id, not position). Promoted-column
population (for SQL queries) and the empty-keyed-collection marker arrive next.
Swap it in with one line: ``database.configure_backend(PostgresRepository())``.
"""

from typing import Any, Iterator

from sqlalchemy import select

from config.data_layout import DEFAULT_MODE, SCENARIO_MODES

from .. import artifacts
from ..base import Repository
from . import _objectstore
from ._columns import promoted_columns
from ._models import (
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
from .engine import get_engine, get_session

# Collection artifacts: a whole document shredded into many rows.
#   artifact -> (model, id_column, collection_key, container_type, id_path)
# container_type 'list' → records are doc[key][]; id is nested_get(record, id_path).
# container_type 'dict' → records are doc[key].items(); id is the dict key, cdm the value.
_COLLECTIONS: dict[str, tuple] = {
    "gauge": (Gauge, "gauge_id", "flood_gauges", "list", ("FloodGauge", "Header", "GaugeID")),
    "property": (Property, "property_id", "properties", "list", ("PropertyHeader", "Header", "PropertyID")),
    "loan": (Loan, "rloan_id", "loans", "list", ("RLoan", "Header", "RLoanID")),
    "commercial": (Commercial, "commercial_id", "commercial_assets", "list", ("CommercialAsset", "Header", "PropertyID")),
    "commercial_loan": (CommercialLoan, "mortgage_id", "commercial_loans", "list", ("Mortgage", "Header", "MortgageID")),
    "counterparty": (Counterparty, "party_id", "counterparties", "list", ("CounterpartySet", "Party", "PartyID")),
    "gauge_hazard_curve": (GaugeHazardCurve, "gauge_id", "hazard_curves", "dict", None),
}

# Keyed artifacts: one row per key.  artifact -> (model, id_column)
_KEYED: dict[str, tuple] = {
    "prs_trade": (PrsTrade, "swap_id"),
    "eod_snapshot": (EodSnapshot, "eod_date"),
}

# Document artifacts: a whole JSON document stored verbatim in one PortDocument
# row per (catchment, artifact, mode) — every DOCUMENT-kind artifact in the
# registry that is NOT shredded into a relational collection above.
_DOCUMENTS: frozenset = frozenset(
    name for name in artifacts.names() if artifacts.spec(name).kind == artifacts.DOCUMENT
) - frozenset(_COLLECTIONS)

# Keyed-record artifacts: a directory of one JSON file per key (timeseries,
# stress storms, sequence gauges, typhoon events), stored one PortRecord row per
# (catchment, artifact, mode, key) — every KEYED-kind artifact NOT given a
# bespoke table above.
_KEYED_DOCS: frozenset = frozenset(
    name for name in artifacts.names() if artifacts.spec(name).kind == artifacts.KEYED
) - frozenset(_KEYED)

# Blob artifacts: binary payloads (classifiers, typhoon particle files) too large
# / opaque for a JSON column. Bytes live in the object store; one PortBlob row per
# (catchment, artifact, mode, key) records that it exists and where.
_BLOBS: frozenset = frozenset(
    name for name in artifacts.names() if artifacts.spec(name).kind == artifacts.BLOB
)


def _object_key(catchment: str, artifact: str, mode: str, key: str) -> str:
    """Deterministic object-store path for one blob."""
    return f"{catchment}/{artifact}/{mode}/{key}"


def modes_for(artifact: str) -> list[str]:
    """Scenario modes a document artifact is persisted under: just the default
    for mode-invariant ones, every distinct-location mode for mode-varying ones
    (property/commercial hazard curves, the flood summary)."""
    sp = artifacts.spec(artifact)
    base = sp.location(DEFAULT_MODE)
    modes = [DEFAULT_MODE]
    for mode in SCENARIO_MODES:
        if mode == DEFAULT_MODE:
            continue
        try:
            location = sp.location(mode)
        except KeyError:
            continue
        if location != base:
            modes.append(mode)
    return modes


def _nested_get(record: dict, path: tuple) -> Any:
    cur = record
    for part in path:
        cur = cur[part]
    return cur


class PostgresRepository(Repository):
    """Repository backed by PostgreSQL (the relational schema under ``_pg``)."""

    # -- helpers ------------------------------------------------------------
    def _ensure_catchment(self, session, catchment: str) -> None:
        if session.get(Catchment, catchment) is None:
            session.add(Catchment(id=catchment))
            session.flush()

    def _model_for(self, artifact: str):
        if artifact in _COLLECTIONS:
            return _COLLECTIONS[artifact][0], _COLLECTIONS[artifact][1]
        if artifact in _KEYED:
            return _KEYED[artifact]
        self._unmapped(artifact)

    @staticmethod
    def _unmapped(artifact: str):
        raise NotImplementedError(
            f"PostgresRepository: artifact '{artifact}' is not yet mapped to a table"
        )

    # -- save ---------------------------------------------------------------
    def save(self, artifact, catchment, payload, key=None, *, mode=DEFAULT_MODE) -> None:
        if artifact in _COLLECTIONS:
            self._save_collection(artifact, catchment, payload, mode)
        elif artifact in _KEYED:
            self._save_keyed(artifact, catchment, payload, key)
        elif artifact in _DOCUMENTS:
            self._save_document(artifact, catchment, payload, mode)
        elif artifact in _KEYED_DOCS:
            self._save_record(artifact, catchment, payload, key, mode)
        elif artifact in _BLOBS:
            self._save_blob(artifact, catchment, payload, key, mode)
        else:
            self._unmapped(artifact)

    def _save_blob(self, artifact, catchment, payload, key, mode) -> None:
        object_key = _object_key(catchment, artifact, mode, key)
        _objectstore.put_bytes(object_key, payload)
        with get_session() as session:
            self._ensure_catchment(session, catchment)
            existing = session.get(PortBlob, (catchment, artifact, mode, key))
            if existing is not None:
                existing.object_key = object_key
                existing.size_bytes = len(payload)
            else:
                session.add(PortBlob(catchment_id=catchment, artifact=artifact, mode=mode,
                                     key=key, object_key=object_key, size_bytes=len(payload)))
            session.commit()

    def _save_document(self, artifact, catchment, payload, mode) -> None:
        with get_session() as session:
            self._ensure_catchment(session, catchment)
            existing = session.get(PortDocument, (catchment, artifact, mode))
            if existing is not None:
                existing.cdm = payload
            else:
                session.add(PortDocument(catchment_id=catchment, artifact=artifact,
                                         mode=mode, cdm=payload))
            session.commit()

    def _save_record(self, artifact, catchment, payload, key, mode) -> None:
        with get_session() as session:
            self._ensure_catchment(session, catchment)
            existing = session.get(PortRecord, (catchment, artifact, mode, key))
            if existing is not None:
                existing.cdm = payload
            else:
                session.add(PortRecord(catchment_id=catchment, artifact=artifact,
                                       mode=mode, key=key, cdm=payload))
            session.commit()

    def _save_collection(self, artifact, catchment, doc, mode) -> None:
        model, id_col, ckey, ctype, id_path = _COLLECTIONS[artifact]
        envelope = {k: v for k, v in doc.items() if k != ckey}
        with get_session() as session:
            self._ensure_catchment(session, catchment)
            # Whole-document replace: clear prior rows + the prior run.
            session.query(model).filter_by(catchment_id=catchment).delete()
            session.query(PortRun).filter_by(catchment_id=catchment, artifact=artifact).delete()
            run = PortRun(catchment_id=catchment, artifact=artifact, mode=mode,
                          generation_metadata=envelope)
            session.add(run)
            session.flush()
            for rec_id, rec in self._iter_records(doc.get(ckey), ctype, id_path):
                session.add(model(catchment_id=catchment, port_run_id=run.id,
                                  cdm=rec, **{id_col: rec_id},
                                  **promoted_columns(artifact, rec)))
            session.commit()

    def _save_keyed(self, artifact, catchment, payload, key) -> None:
        model, id_col = _KEYED[artifact]
        with get_session() as session:
            self._ensure_catchment(session, catchment)
            cols = promoted_columns(artifact, payload)
            existing = session.get(model, (catchment, key))
            if existing is not None:
                existing.cdm = payload
                for col, val in cols.items():
                    setattr(existing, col, val)
            else:
                session.add(model(catchment_id=catchment, cdm=payload, **{id_col: key}, **cols))
            session.commit()

    @staticmethod
    def _iter_records(container, ctype, id_path):
        if ctype == "dict":
            for rec_id, rec in (container or {}).items():
                yield rec_id, rec
        else:
            for rec in (container or []):
                yield _nested_get(rec, id_path), rec

    # -- load ---------------------------------------------------------------
    def load(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> Any:
        if artifact in _COLLECTIONS:
            return self._load_collection(artifact, catchment)
        if artifact in _KEYED:
            return self._load_keyed(artifact, catchment, key)
        if artifact in _DOCUMENTS:
            return self._load_document(artifact, catchment, mode)
        if artifact in _KEYED_DOCS:
            return self._load_record(artifact, catchment, key, mode)
        if artifact in _BLOBS:
            return self._load_blob(artifact, catchment, key, mode)
        self._unmapped(artifact)

    def _load_blob(self, artifact, catchment, key, mode) -> bytes:
        with get_session() as session:
            row = session.get(PortBlob, (catchment, artifact, mode, key))
            if row is None:
                raise FileNotFoundError(
                    f"{artifact}[{key}] not found for catchment '{catchment}' (mode '{mode}')")
            object_key = row.object_key
        return _objectstore.get_bytes(object_key)

    def _load_document(self, artifact, catchment, mode) -> Any:
        with get_session() as session:
            row = session.get(PortDocument, (catchment, artifact, mode))
            if row is None:
                raise FileNotFoundError(
                    f"{artifact} not found for catchment '{catchment}' (mode '{mode}')")
            return row.cdm

    def _load_record(self, artifact, catchment, key, mode) -> Any:
        with get_session() as session:
            row = session.get(PortRecord, (catchment, artifact, mode, key))
            if row is None:
                raise FileNotFoundError(
                    f"{artifact}[{key}] not found for catchment '{catchment}' (mode '{mode}')")
            return row.cdm

    def _load_collection(self, artifact, catchment) -> Any:
        model, id_col, ckey, ctype, _ = _COLLECTIONS[artifact]
        with get_session() as session:
            run = session.query(PortRun).filter_by(
                catchment_id=catchment, artifact=artifact).first()
            if run is None:
                raise FileNotFoundError(f"{artifact} not found for catchment '{catchment}'")
            rows = session.scalars(
                select(model).filter_by(catchment_id=catchment)
                .order_by(getattr(model, id_col))
            ).all()
            if ctype == "dict":
                records: Any = {getattr(r, id_col): r.cdm for r in rows}
            else:
                records = [r.cdm for r in rows]
            return {**(run.generation_metadata or {}), ckey: records}

    def _load_keyed(self, artifact, catchment, key) -> Any:
        model, _ = _KEYED[artifact]
        with get_session() as session:
            row = session.get(model, (catchment, key))
            if row is None:
                raise FileNotFoundError(f"{artifact}[{key}] not found for catchment '{catchment}'")
            return row.cdm

    # -- delete / iter / exists --------------------------------------------
    def delete(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> None:
        if artifact in _COLLECTIONS:
            model = _COLLECTIONS[artifact][0]
            with get_session() as session:
                session.query(model).filter_by(catchment_id=catchment).delete()
                session.query(PortRun).filter_by(catchment_id=catchment, artifact=artifact).delete()
                session.commit()
        elif artifact in _KEYED:
            model, _ = _KEYED[artifact]
            with get_session() as session:
                row = session.get(model, (catchment, key))
                if row is not None:
                    session.delete(row)
                session.commit()
        elif artifact in _DOCUMENTS:
            with get_session() as session:
                row = session.get(PortDocument, (catchment, artifact, mode))
                if row is not None:
                    session.delete(row)
                session.commit()
        elif artifact in _KEYED_DOCS:
            with get_session() as session:
                row = session.get(PortRecord, (catchment, artifact, mode, key))
                if row is not None:
                    session.delete(row)
                session.commit()
        elif artifact in _BLOBS:
            with get_session() as session:
                row = session.get(PortBlob, (catchment, artifact, mode, key))
                object_key = row.object_key if row is not None else None
                if row is not None:
                    session.delete(row)
                session.commit()
            if object_key is not None:
                _objectstore.delete_object(object_key)
        else:
            self._unmapped(artifact)

    def iter_keys(self, artifact, catchment, *, mode=DEFAULT_MODE) -> Iterator[str]:
        if artifact in _DOCUMENTS:
            return iter(())                      # documents are whole-doc, not keyed
        if artifact in _KEYED_DOCS:
            with get_session() as session:
                keys = session.scalars(
                    select(PortRecord.key)
                    .filter_by(catchment_id=catchment, artifact=artifact, mode=mode)
                    .order_by(PortRecord.key)
                ).all()
            return iter(keys)
        if artifact in _BLOBS:
            with get_session() as session:
                keys = session.scalars(
                    select(PortBlob.key)
                    .filter_by(catchment_id=catchment, artifact=artifact, mode=mode)
                    .order_by(PortBlob.key)
                ).all()
            return iter(keys)
        model, id_col = self._model_for(artifact)
        with get_session() as session:
            ids = session.scalars(
                select(getattr(model, id_col)).filter_by(catchment_id=catchment)
                .order_by(getattr(model, id_col))
            ).all()
        return iter(ids)

    def exists(self, artifact, catchment, key=None, *, mode=DEFAULT_MODE) -> bool:
        if artifact in _COLLECTIONS:
            with get_session() as session:
                return session.query(PortRun).filter_by(
                    catchment_id=catchment, artifact=artifact).first() is not None
        if artifact in _DOCUMENTS:
            with get_session() as session:
                return session.get(PortDocument, (catchment, artifact, mode)) is not None
        if artifact in _KEYED_DOCS:
            with get_session() as session:
                return session.get(PortRecord, (catchment, artifact, mode, key)) is not None
        if artifact in _BLOBS:
            with get_session() as session:
                return session.get(PortBlob, (catchment, artifact, mode, key)) is not None
        if artifact in _KEYED:
            model, _ = _KEYED[artifact]
            with get_session() as session:
                return session.get(model, (catchment, key)) is not None
        self._unmapped(artifact)

    def has_collection(self, artifact, catchment, *, mode=DEFAULT_MODE) -> bool:
        if artifact in _DOCUMENTS:                # mirrors file backend: doc present
            return self.exists(artifact, catchment, mode=mode)
        if artifact in _KEYED_DOCS:
            with get_session() as session:
                return session.query(PortRecord).filter_by(
                    catchment_id=catchment, artifact=artifact, mode=mode).first() is not None
        if artifact in _BLOBS:
            with get_session() as session:
                return session.query(PortBlob).filter_by(
                    catchment_id=catchment, artifact=artifact, mode=mode).first() is not None
        model, id_col = self._model_for(artifact)
        with get_session() as session:
            return session.query(model).filter_by(catchment_id=catchment).first() is not None

    def catchments(self) -> list[str]:
        with get_session() as session:
            ids = session.scalars(select(Catchment.id).order_by(Catchment.id)).all()
        return list(ids)

    def ping(self) -> bool:
        try:
            with get_engine().connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return True
        except Exception:
            return False
