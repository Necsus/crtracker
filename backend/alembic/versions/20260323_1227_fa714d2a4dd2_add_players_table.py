"""add_players_table

Revision ID: fa714d2a4dd2
Revises:
Create Date: 2026-03-23 12:27:56.445182
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa714d2a4dd2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        # Identity
        sa.Column('tag', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        # Progression
        sa.Column('exp_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exp_points', sa.Integer(), nullable=True),
        sa.Column('total_exp_points', sa.Integer(), nullable=True),
        sa.Column('star_points', sa.Integer(), nullable=True),
        # Trophy Road
        sa.Column('trophies', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('best_trophies', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('legacy_trophy_road_high_score', sa.Integer(), nullable=True),
        # Battle stats
        sa.Column('wins', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losses', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('battle_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('three_crown_wins', sa.Integer(), nullable=False, server_default='0'),
        # Challenge & tournament
        sa.Column('challenge_cards_won', sa.Integer(), nullable=True),
        sa.Column('challenge_max_wins', sa.Integer(), nullable=True),
        sa.Column('tournament_cards_won', sa.Integer(), nullable=True),
        sa.Column('tournament_battle_count', sa.Integer(), nullable=True),
        # Clan & social
        sa.Column('war_day_wins', sa.Integer(), nullable=True),
        sa.Column('clan_cards_collected', sa.Integer(), nullable=True),
        sa.Column('donations', sa.Integer(), nullable=True),
        sa.Column('donations_received', sa.Integer(), nullable=True),
        sa.Column('total_donations', sa.Integer(), nullable=True),
        sa.Column('clan_tag', sa.String(length=20), nullable=True),
        sa.Column('clan_name', sa.String(length=100), nullable=True),
        sa.Column('clan_badge_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        # Arena
        sa.Column('arena_id', sa.Integer(), nullable=True),
        sa.Column('arena_name', sa.String(length=50), nullable=True),
        # Path of Legends
        sa.Column('pol_league_number', sa.Integer(), nullable=True),
        sa.Column('pol_trophies', sa.Integer(), nullable=True),
        sa.Column('pol_rank', sa.Integer(), nullable=True),
        # JSONB blobs
        sa.Column('current_deck', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('current_favourite_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('league_statistics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('badges', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('achievements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        # Audit
        sa.Column('last_synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag', name='uq_players_tag'),
    )
    op.create_index('ix_players_tag', 'players', ['tag'], unique=True)
    op.create_index('ix_players_trophies', 'players', ['trophies'], unique=False)
    op.create_index('ix_players_clan_tag', 'players', ['clan_tag'], unique=False)
    op.create_index('ix_players_pol_league_number', 'players', ['pol_league_number'], unique=False)
    op.create_index('ix_players_pol_rank', 'players', ['pol_rank'], unique=False)


def downgrade() -> None:
    op.drop_table('players')
    op.create_table('player_season_ranks',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('player_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('season_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('league_rank', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('league_number', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('trophies', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('synced_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['player_id'], ['players.id'], name=op.f('fk_psr_player_id'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], name=op.f('fk_psr_season_id'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('player_season_ranks_pkey')),
    sa.UniqueConstraint('player_id', 'season_id', name=op.f('uq_player_season'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_player_season_ranks_season_id'), 'player_season_ranks', ['season_id'], unique=False)
    op.create_index(op.f('ix_player_season_ranks_player_id'), 'player_season_ranks', ['player_id'], unique=False)
    op.create_index(op.f('ix_player_season_ranks_league_rank'), 'player_season_ranks', ['league_rank'], unique=False)
    op.create_table('seasons',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('start_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('end_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('seasons_pkey')),
    sa.UniqueConstraint('name', name=op.f('uq_seasons_name'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_seasons_name'), 'seasons', ['name'], unique=True)
    op.create_table('battles',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('battle_key', sa.VARCHAR(length=120), autoincrement=False, nullable=False),
    sa.Column('battle_time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('battle_type', sa.VARCHAR(length=40), autoincrement=False, nullable=True),
    sa.Column('game_mode_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('game_mode_name', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('arena_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('arena_name', sa.VARCHAR(length=80), autoincrement=False, nullable=True),
    sa.Column('team1_tag', sa.VARCHAR(length=15), autoincrement=False, nullable=False),
    sa.Column('team1_name', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('team1_crowns', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team1_starting_trophies', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team1_trophy_change', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team1_cards', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('team2_tag', sa.VARCHAR(length=15), autoincrement=False, nullable=False),
    sa.Column('team2_name', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('team2_crowns', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team2_starting_trophies', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team2_trophy_change', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('team2_cards', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('winner_tag', sa.VARCHAR(length=15), autoincrement=False, nullable=True),
    sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('battles_pkey')),
    sa.UniqueConstraint('battle_key', name=op.f('uq_battles_battle_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_battles_winner_tag'), 'battles', ['winner_tag'], unique=False)
    op.create_index(op.f('ix_battles_team2_tag'), 'battles', ['team2_tag'], unique=False)
    op.create_index(op.f('ix_battles_team1_tag'), 'battles', ['team1_tag'], unique=False)
    op.create_index(op.f('ix_battles_battle_type'), 'battles', ['battle_type'], unique=False)
    op.create_index(op.f('ix_battles_battle_time'), 'battles', ['battle_time'], unique=False)
    op.create_index(op.f('ix_battles_battle_key'), 'battles', ['battle_key'], unique=True)
    op.create_table('deck_meta_statuses',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('deck_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('season_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(length=20), server_default=sa.text("'UNCLASSIFIED'::character varying"), autoincrement=False, nullable=False),
    sa.Column('usage_rate', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('winrate', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('sample_size', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('computed_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], name=op.f('fk_deck_meta_statuses_deck_id'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['season_id'], ['seasons.id'], name=op.f('fk_deck_meta_statuses_season_id'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('deck_meta_statuses_pkey')),
    sa.UniqueConstraint('deck_id', 'season_id', name=op.f('uq_deck_season_status'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_deck_meta_statuses_season_id'), 'deck_meta_statuses', ['season_id'], unique=False)
    op.create_index(op.f('ix_deck_meta_statuses_deck_id'), 'deck_meta_statuses', ['deck_id'], unique=False)
    op.create_table('archetypes',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('win_condition', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('play_style', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('is_timeless', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False),
    sa.Column('variant_of_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('core_cards', postgresql.JSON(astext_type=sa.Text()), server_default=sa.text("'[]'::json"), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['variant_of_id'], ['archetypes.id'], name=op.f('fk_archetypes_variant_of_id'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('archetypes_pkey')),
    sa.UniqueConstraint('name', name=op.f('uq_archetypes_name'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_archetypes_variant_of_id'), 'archetypes', ['variant_of_id'], unique=False)
    op.create_index(op.f('ix_archetypes_name'), 'archetypes', ['name'], unique=True)
    op.create_index(op.f('ix_archetypes_is_timeless'), 'archetypes', ['is_timeless'], unique=False)
    op.create_table('decks',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('archetype', sa.VARCHAR(length=50), autoincrement=False, nullable=False),
    sa.Column('cards', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('avg_elixir', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('player_tag', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    sa.Column('matchup_stats', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('oracle_cache', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('archetype_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('deck_key', sa.VARCHAR(length=40), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['archetype_id'], ['archetypes.id'], name=op.f('fk_decks_archetype_id'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('decks_pkey'))
    )
    op.create_index(op.f('ix_decks_player_tag'), 'decks', ['player_tag'], unique=False)
    op.create_index(op.f('ix_decks_name'), 'decks', ['name'], unique=False)
    op.create_index(op.f('ix_decks_deck_key'), 'decks', ['deck_key'], unique=False)
    op.create_index(op.f('ix_decks_archetype_id'), 'decks', ['archetype_id'], unique=False)
    op.create_index(op.f('ix_decks_archetype'), 'decks', ['archetype'], unique=False)
    op.create_table('cards',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('card_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('rarity', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('card_type', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('elixir_cost', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('max_level', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('max_evolution_level', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('deploy_time', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('speed', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('arena_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('target', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('icon_url_medium', sa.VARCHAR(length=512), autoincrement=False, nullable=True),
    sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('cards_pkey')),
    sa.UniqueConstraint('card_id', name=op.f('uq_cards_card_id'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_cards_rarity'), 'cards', ['rarity'], unique=False)
    op.create_index(op.f('ix_cards_name'), 'cards', ['name'], unique=False)
    op.create_index(op.f('ix_cards_card_id'), 'cards', ['card_id'], unique=True)
    # ### end Alembic commands ###
