"""Add archetypes and deck_meta_statuses tables; patch decks with archetype_id and deck_key.

Revision ID: 006
Revises: 005
Create Date: 2026-03-18

Changes:
  - NEW TABLE archetypes          (curated, permanent archetype catalogue)
  - NEW TABLE deck_meta_statuses  (per-season competitive status, computed from battles)
  - ADD COLUMN decks.archetype_id FK → archetypes.id  (nullable, populated by fingerprinter)
  - ADD COLUMN decks.deck_key     SHA-1 fingerprint of sorted card IDs (nullable, indexed)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # archetypes
    # ------------------------------------------------------------------
    op.create_table(
        "archetypes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # Human-readable name, e.g. "Hog 2.6", "Hog Cycle", "Golem Beatdown"
        sa.Column("name", sa.String(length=100), nullable=False),
        # Primary win condition card slug, e.g. "hog-rider", "golem", "x-bow"
        sa.Column("win_condition", sa.String(length=50), nullable=False),
        # Structural play style: CYCLE | BEATDOWN | CONTROL | BRIDGE_SPAM | SIEGE | HYBRID
        sa.Column("play_style", sa.String(length=20), nullable=False),
        # "Indemodable" flag — set manually for archetypes that have existed for years
        sa.Column(
            "is_timeless",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        # Self-referential FK: a variant points to its parent archetype
        # e.g. "Hog 2.6" → "Hog Cycle", "Hog 3.0" → "Hog Cycle"
        sa.Column("variant_of_id", sa.Integer(), nullable=True),
        # Ordered list of card slugs that MUST be present in a deck for it to match
        # this archetype. More cards = more specific = higher priority in fingerprinting.
        # e.g. ["hog-rider", "ice-golem", "ice-spirit", "skeletons"] for Hog 2.6
        sa.Column("core_cards", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["variant_of_id"],
            ["archetypes.id"],
            name="fk_archetypes_variant_of_id",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_archetypes_name"),
    )
    op.create_index(op.f("ix_archetypes_name"), "archetypes", ["name"], unique=True)
    op.create_index(
        op.f("ix_archetypes_is_timeless"), "archetypes", ["is_timeless"], unique=False
    )
    op.create_index(
        op.f("ix_archetypes_variant_of_id"),
        "archetypes",
        ["variant_of_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # deck_meta_statuses
    # Computed by a periodic job from battle logs, one row per (deck × season).
    # status values: DOMINANT | VIABLE | ANTI_META | OFF_META | UNCLASSIFIED
    # ------------------------------------------------------------------
    op.create_table(
        "deck_meta_statuses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("deck_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="UNCLASSIFIED",
        ),
        # Percentage of top-ladder battles in which this deck appeared
        sa.Column("usage_rate", sa.Float(), nullable=True),
        # Overall winrate (0-100) for this deck this season
        sa.Column("winrate", sa.Float(), nullable=True),
        # Number of battles used to compute these stats
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["deck_id"],
            ["decks.id"],
            name="fk_deck_meta_statuses_deck_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["seasons.id"],
            name="fk_deck_meta_statuses_season_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_id", "season_id", name="uq_deck_season_status"),
    )
    op.create_index(
        op.f("ix_deck_meta_statuses_deck_id"),
        "deck_meta_statuses",
        ["deck_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_deck_meta_statuses_season_id"),
        "deck_meta_statuses",
        ["season_id"],
        unique=False,
    )

    # ------------------------------------------------------------------
    # Patch decks table
    # ------------------------------------------------------------------
    # archetype_id: nullable FK so existing decks are not broken; populated
    # progressively by the fingerprinting service.
    op.add_column(
        "decks",
        sa.Column("archetype_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_decks_archetype_id",
        "decks",
        "archetypes",
        ["archetype_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_decks_archetype_id"), "decks", ["archetype_id"], unique=False
    )

    # deck_key: SHA-1 of sorted card IDs, production of from the fingerprinting
    # service. Replaces the embedded matchup_stats["deck_key"] JSON field over time.
    op.add_column(
        "decks",
        sa.Column("deck_key", sa.String(length=40), nullable=True),
    )
    op.create_index(op.f("ix_decks_deck_key"), "decks", ["deck_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_decks_deck_key"), table_name="decks")
    op.drop_column("decks", "deck_key")

    op.drop_index(op.f("ix_decks_archetype_id"), table_name="decks")
    op.drop_constraint("fk_decks_archetype_id", "decks", type_="foreignkey")
    op.drop_column("decks", "archetype_id")

    op.drop_index(
        op.f("ix_deck_meta_statuses_season_id"), table_name="deck_meta_statuses"
    )
    op.drop_index(
        op.f("ix_deck_meta_statuses_deck_id"), table_name="deck_meta_statuses"
    )
    op.drop_table("deck_meta_statuses")

    op.drop_index(op.f("ix_archetypes_variant_of_id"), table_name="archetypes")
    op.drop_index(op.f("ix_archetypes_is_timeless"), table_name="archetypes")
    op.drop_index(op.f("ix_archetypes_name"), table_name="archetypes")
    op.drop_table("archetypes")
