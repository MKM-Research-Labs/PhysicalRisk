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

"""Schema-contract tests for the Postgres relational models (WP1.2).

Pin the promoted-columns + JSONB-tail design so a model change is a deliberate,
visible edit. Pure metadata assertions — no live database. Model↔migration drift
is caught at docker time by ``alembic check`` (autogenerate shows no diff)."""

from database._pg import Base, Catchment, Gauge, PortRun


def test_expected_tables_registered():
    assert set(Base.metadata.tables) == {"catchment", "port_run", "gauge"}


def test_gauge_promoted_columns_and_cdm():
    cols = {c.name for c in Gauge.__table__.columns}
    assert cols == {
        "catchment_id", "gauge_id", "port_run_id", "gauge_name",
        "latitude", "longitude", "elevation",
        "flood_alert", "flood_warning", "severe_flood_warning",
        "nrfa_station_id", "cdm",
    }
    # Full document preserved + non-null for round-trip fidelity.
    assert Gauge.__table__.c.cdm.nullable is False


def test_gauge_composite_primary_key():
    pk = {c.name for c in Gauge.__table__.primary_key.columns}
    assert pk == {"catchment_id", "gauge_id"}  # gauge ids repeat across catchments


def test_gauge_foreign_keys():
    fks = {
        (fk.parent.name, fk.column.table.name)
        for fk in Gauge.__table__.foreign_keys
    }
    assert ("catchment_id", "catchment") in fks
    assert ("port_run_id", "port_run") in fks


def test_port_run_provenance_columns():
    cols = {c.name for c in PortRun.__table__.columns}
    assert cols == {
        "id", "catchment_id", "artifact", "mode",
        "generated_at", "schema_version", "generation_metadata",
    }
    assert {c.name for c in PortRun.__table__.primary_key.columns} == {"id"}


def test_catchment_is_the_fk_anchor():
    assert {c.name for c in Catchment.__table__.primary_key.columns} == {"id"}
