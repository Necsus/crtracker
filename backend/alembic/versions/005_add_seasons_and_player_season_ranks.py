"""Add seasons and player_season_ranks tables.

Revision ID: 005
Revises: 004
Create Date: 2026-03-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # seasons
    # ------------------------------------------------------------------
    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Human-readable label, e.g. '2026-03'
        sa.Column("name", sa.String(length=10), nullable=False),
        # Exact start / end timestamps (timezone-aware).
        # end_at is NULL while the season is still active.
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_seasons_name"),
    )
    op.create_index(op.f("ix_seasons_name"), "seasons", ["name"], unique=True)

    # ------------------------------------------------------------------
    # player_season_ranks
    # ------------------------------------------------------------------
    op.create_table(
        "player_season_ranks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("league_rank", sa.Integer(), nullable=True),
        sa.Column("league_number", sa.Integer(), nullable=True),
        sa.Column("trophies", sa.Integer(), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            name="fk_psr_player_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["seasons.id"],
            name="fk_psr_season_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "season_id", name="uq_player_season"),
    )
    op.create_index(
        op.f("ix_player_season_ranks_player_id"),
        "player_season_ranks",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_player_season_ranks_season_id"),
        "player_season_ranks",
        ["season_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_player_season_ranks_league_rank"),
        "player_season_ranks",
        ["league_rank"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_player_season_ranks_league_rank"),
        table_name="player_season_ranks",
    )
    op.drop_index(
        op.f("ix_player_season_ranks_season_id"),
        table_name="player_season_ranks",
    )
    op.drop_index(
        op.f("ix_player_season_ranks_player_id"),
        table_name="player_season_ranks",
    )
    op.drop_table("player_season_ranks")

    op.drop_index(op.f("ix_seasons_name"), table_name="seasons")
    op.drop_table("seasons")
