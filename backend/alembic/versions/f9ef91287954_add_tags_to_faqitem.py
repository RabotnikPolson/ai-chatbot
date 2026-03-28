"""Add tags to FAQItem

Revision ID: f9ef91287954
Revises: 4b2e301b3e82
Create Date: 2026-03-13 09:06:33.000076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f9ef91287954'
down_revision: Union[str, Sequence[str], None] = '4b2e301b3e82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('faq_items', sa.Column('tags', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('faq_items', 'tags')
