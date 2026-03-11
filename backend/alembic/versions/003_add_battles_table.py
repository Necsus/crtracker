"""Add battles table.

Revision ID: 003
Revises: 002
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "battles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Normalised dedup key: "{battleTime}_{min(tag1,tag2)}_{max(tag1,tag2)}"
        sa.Column("battle_key", sa.String(length=120), nullable=False),
        sa.Column("battle_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("battle_type", sa.String(length=40), nullable=True),
        sa.Column("game_mode_id", sa.Integer(), nullable=True),
        sa.Column("game_mode_name", sa.String(length=80), nullable=True),
        sa.Column("arena_id", sa.Integer(), nullable=True),
        sa.Column("arena_name", sa.String(length=80), nullable=True),
        # Team 1 (alphabetically lower tag)
        sa.Column("team1_tag", sa.String(length=15), nullable=False),
        sa.Column("team1_name", sa.String(length=100), nullable=True),
        sa.Column("team1_crowns", sa.Integer(), nullable=True),
        sa.Column("team1_starting_trophies", sa.Integer(), nullable=True),
        sa.Column("team1_trophy_change", sa.Integer(), nullable=True),
        sa.Column("team1_cards", postgresql.JSON(), nullable=True),
        # Team 2 (alphabetically greater tag)
        sa.Column("team2_tag", sa.String(length=15), nullable=False),
        sa.Column("team2_name", sa.String(length=100), nullable=True),
        sa.Column("team2_crowns", sa.Integer(), nullable=True),
        sa.Column("team2_starting_trophies", sa.Integer(), nullable=True),
        sa.Column("team2_trophy_change", sa.Integer(), nullable=True),
        sa.Column("team2_cards", postgresql.JSON(), nullable=True),
        # Result
        sa.Column("winner_tag", sa.String(length=15), nullable=True),
        # Raw payload
        sa.Column("raw_data", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("battle_key", name="uq_battles_battle_key"),
    )

    op.create_index(op.f("ix_battles_battle_key"), "battles", ["battle_key"], unique=True)
    op.create_index(op.f("ix_battles_battle_time"), "battles", ["battle_time"], unique=False)
    op.create_index(op.f("ix_battles_battle_type"), "battles", ["battle_type"], unique=False)
    op.create_index(op.f("ix_battles_team1_tag"), "battles", ["team1_tag"], unique=False)
    op.create_index(op.f("ix_battles_team2_tag"), "battles", ["team2_tag"], unique=False)
    op.create_index(op.f("ix_battles_winner_tag"), "battles", ["winner_tag"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_battles_winner_tag"), table_name="battles")
    op.drop_index(op.f("ix_battles_team2_tag"), table_name="battles")
    op.drop_index(op.f("ix_battles_team1_tag"), table_name="battles")
    op.drop_index(op.f("ix_battles_battle_type"), table_name="battles")
    op.drop_index(op.f("ix_battles_battle_time"), table_name="battles")
    op.drop_index(op.f("ix_battles_battle_key"), table_name="battles")
    op.drop_table("battles")
