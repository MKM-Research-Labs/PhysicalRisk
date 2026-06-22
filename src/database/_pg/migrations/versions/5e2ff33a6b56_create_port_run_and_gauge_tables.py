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

"""create port_run and gauge tables

Revision ID: 5e2ff33a6b56
Revises: 7c0b91c7c73c
Create Date: 2026-06-22 11:07:48.471434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '5e2ff33a6b56'
down_revision: Union[str, None] = '7c0b91c7c73c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "port_run",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("catchment_id", sa.String(), sa.ForeignKey("catchment.id"), nullable=False),
        sa.Column("artifact", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("schema_version", sa.String(), nullable=True),
        sa.Column("generation_metadata", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_port_run_catchment_id", "port_run", ["catchment_id"])

    op.create_table(
        "gauge",
        sa.Column("catchment_id", sa.String(), sa.ForeignKey("catchment.id"), primary_key=True),
        sa.Column("gauge_id", sa.String(), primary_key=True),
        sa.Column("port_run_id", sa.Integer(), sa.ForeignKey("port_run.id"), nullable=True),
        sa.Column("gauge_name", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("elevation", sa.Float(), nullable=True),
        sa.Column("flood_alert", sa.Float(), nullable=True),
        sa.Column("flood_warning", sa.Float(), nullable=True),
        sa.Column("severe_flood_warning", sa.Float(), nullable=True),
        sa.Column("nrfa_station_id", sa.String(), nullable=True),
        sa.Column("cdm", postgresql.JSONB(), nullable=False),
    )
    op.create_index("ix_gauge_port_run_id", "gauge", ["port_run_id"])
    op.create_index("ix_gauge_nrfa_station_id", "gauge", ["nrfa_station_id"])


def downgrade() -> None:
    op.drop_table("gauge")
    op.drop_table("port_run")
