"""initial_schema

Revision ID: f5747e5233a3
Revises: 
Create Date: 2026-10-24 13:05:17.760641

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5747e5233a3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    from app.adapters.db.session import Base
    import app.adapters.db.models  # noqa: F401
    Base.metadata.create_all(bind=conn)


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    from app.adapters.db.session import Base
    import app.adapters.db.models  # noqa: F401
    Base.metadata.drop_all(bind=conn)
