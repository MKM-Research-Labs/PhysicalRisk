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
