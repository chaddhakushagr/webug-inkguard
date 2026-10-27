"""add_verifier_fields_to_findings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-28 03:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('findings', sa.Column('verifier_verdict', sa.String(length=32), nullable=True))
    op.add_column('findings', sa.Column('verifier_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('findings', 'verifier_reason')
    op.drop_column('findings', 'verifier_verdict')
