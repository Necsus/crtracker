"""Add players table.

Revision ID: 004
Revises: 003
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Normalised tag WITHOUT the leading '#'
        sa.Column("tag", sa.String(length=15), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("trophies", sa.Integer(), nullable=True),
        sa.Column("best_trophies", sa.Integer(), nullable=True),
        sa.Column("exp_level", sa.Integer(), nullable=True),
        sa.Column("wins", sa.Integer(), nullable=True),
        sa.Column("losses", sa.Integer(), nullable=True),
        sa.Column("battle_count", sa.Integer(), nullable=True),
        # Path of Legend specific fields
        sa.Column("league_number", sa.Integer(), nullable=True),
        sa.Column("league_rank", sa.Integer(), nullable=True),   # rank on the global leaderboard
        sa.Column("season", sa.String(length=10), nullable=True),  # e.g. '2026-03'
        # Current deck – JSON array of card objects from the CR API
        sa.Column("current_deck", postgresql.JSON(), nullable=True),
        # Full raw profile payload
        sa.Column("raw_data", postgresql.JSON(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tag", name="uq_players_tag"),
    )

    op.create_index(op.f("ix_players_tag"), "players", ["tag"], unique=True)
    op.create_index(op.f("ix_players_name"), "players", ["name"], unique=False)
    op.create_index(op.f("ix_players_trophies"), "players", ["trophies"], unique=False)
    op.create_index(op.f("ix_players_league_rank"), "players", ["league_rank"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_players_league_rank"), table_name="players")
    op.drop_index(op.f("ix_players_trophies"), table_name="players")
    op.drop_index(op.f("ix_players_name"), table_name="players")
    op.drop_index(op.f("ix_players_tag"), table_name="players")
    op.drop_table("players")
