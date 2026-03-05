"""Add cards table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        # CR API numeric identifier (unique)
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        # Rarity: Common / Rare / Epic / Legendary / Champion
        sa.Column("rarity", sa.String(length=20), nullable=False),
        # Type: Troop / Building / Spell
        sa.Column("card_type", sa.String(length=20), nullable=True),
        sa.Column("elixir_cost", sa.Integer(), nullable=True),
        sa.Column("max_level", sa.Integer(), nullable=False),
        sa.Column("max_evolution_level", sa.Integer(), nullable=True),
        sa.Column("deploy_time", sa.Integer(), nullable=True),
        # Speed: Slow / Medium / Fast / Very Fast
        sa.Column("speed", sa.String(length=20), nullable=True),
        sa.Column("arena_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        # JSON array of target types, e.g. ["Ground", "Air"]
        sa.Column("target", postgresql.JSON(), nullable=True),
        sa.Column("icon_url_medium", sa.String(length=512), nullable=True),
        # Full raw CR API payload for forward-compatibility
        sa.Column("raw_data", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("card_id", name="uq_cards_card_id"),
    )

    op.create_index(op.f("ix_cards_card_id"), "cards", ["card_id"], unique=True)
    op.create_index(op.f("ix_cards_name"), "cards", ["name"], unique=False)
    op.create_index(op.f("ix_cards_rarity"), "cards", ["rarity"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cards_rarity"), table_name="cards")
    op.drop_index(op.f("ix_cards_name"), table_name="cards")
    op.drop_index(op.f("ix_cards_card_id"), table_name="cards")
    op.drop_table("cards")
