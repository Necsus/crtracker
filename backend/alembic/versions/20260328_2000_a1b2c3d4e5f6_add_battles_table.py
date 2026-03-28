"""add_battles_table

Revision ID: a1b2c3d4e5f6
Revises: fa714d2a4dd2
Create Date: 2026-03-28 20:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fa714d2a4dd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'battles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player_tag', sa.String(length=20), nullable=False),
        sa.Column('battle_key', sa.String(length=120), nullable=False),
        sa.Column('battle_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('battle_type', sa.String(length=40), nullable=True),
        sa.Column('game_mode_name', sa.String(length=80), nullable=True),
        sa.Column('arena_name', sa.String(length=80), nullable=True),
        sa.Column('result', sa.String(length=10), nullable=False),
        sa.Column('trophy_change', sa.Integer(), nullable=True),
        sa.Column('player_crowns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opponent_tag', sa.String(length=20), nullable=True),
        sa.Column('opponent_name', sa.String(length=100), nullable=True),
        sa.Column('opponent_crowns', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opponent_trophies', sa.Integer(), nullable=True),
        sa.Column('player_cards', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('opponent_cards', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('battle_key', name='uq_battles_battle_key'),
    )
    op.create_index('ix_battles_player_tag', 'battles', ['player_tag'])
    op.create_index('ix_battles_battle_time', 'battles', ['battle_time'])


def downgrade() -> None:
    op.drop_index('ix_battles_battle_time', table_name='battles')
    op.drop_index('ix_battles_player_tag', table_name='battles')
    op.drop_table('battles')
