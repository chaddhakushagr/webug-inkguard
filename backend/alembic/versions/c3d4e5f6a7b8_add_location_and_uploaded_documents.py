"""add_location_and_uploaded_documents

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-10-28 09:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add location and cited_entry_code columns to findings
    with op.batch_alter_table('findings') as batch_op:
        batch_op.add_column(sa.Column('location', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('cited_entry_code', sa.String(length=50), nullable=True))

    # 2. Create uploaded_documents table
    op.create_table(
        'uploaded_documents',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('submission_id', sa.String(length=36), sa.ForeignKey('submissions.id'), nullable=False, index=True),
        sa.Column('submission_version_id', sa.String(length=36), sa.ForeignKey('submission_versions.id'), nullable=False, index=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('data', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('uploaded_documents')
    with op.batch_alter_table('findings') as batch_op:
        batch_op.drop_column('cited_entry_code')
        batch_op.drop_column('location')
