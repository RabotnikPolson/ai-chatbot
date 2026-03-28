"""Add public_id UUID field to messages

Revision ID: c7f4e0a8d1b1
Revises: f9ef91287954
Create Date: 2026-03-24 16:20:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = "c7f4e0a8d1b1"
down_revision: Union[str, Sequence[str], None] = "f9ef91287954"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("public_id", sa.String(length=36), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT id FROM messages")).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE messages SET public_id = :public_id WHERE id = :id"),
            {"public_id": str(uuid.uuid4()), "id": row[0]},
        )

    op.alter_column("messages", "public_id", nullable=False)
    op.create_index("ix_messages_public_id", "messages", ["public_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_messages_public_id", table_name="messages")
    op.drop_column("messages", "public_id")

