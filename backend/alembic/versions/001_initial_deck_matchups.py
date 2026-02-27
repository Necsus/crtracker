"""Initial deck and matchup tables.

Revision ID: 001
Revises:
Create Date: 2025-01-15 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create decks table
    op.create_table(
        "decks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("archetype", sa.String(length=50), nullable=False),
        sa.Column("cards", postgresql.JSON(), nullable=False),
        sa.Column("avg_elixir", sa.Float(), nullable=False),
        sa.Column("player_tag", sa.String(length=10), nullable=True),
        sa.Column("matchup_stats", postgresql.JSON(), nullable=False),
        sa.Column("oracle_cache", postgresql.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(op.f("ix_decks_archetype"), "decks", ["archetype"], unique=False)
    op.create_index(op.f("ix_decks_name"), "decks", ["name"], unique=False)
    op.create_index(op.f("ix_decks_player_tag"), "decks", ["player_tag"], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f("ix_decks_player_tag"), table_name="decks")
    op.drop_index(op.f("ix_decks_name"), table_name="decks")
    op.drop_index(op.f("ix_decks_archetype"), table_name="decks")

    # Drop table
    op.drop_table("decks")
