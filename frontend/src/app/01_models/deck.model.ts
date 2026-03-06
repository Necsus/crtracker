/* ============================================
   DECK MODELS
   TypeScript interfaces mirroring backend Pydantic schemas
   ============================================ */

/**
 * Represents a single Clash Royale card
 */
export interface Card {
  id: string;
  name: string;
  elixir: number;
  rarity: 'common' | 'rare' | 'epic' | 'legendary' | 'champion';
  type?: 'troop' | 'spell' | 'building';
  icon_url?: string;
}

/**
 * Lightweight deck representation for list views
 */
export interface DeckListItem {
  id: number;
  name: string;
  archetype: string;
  avg_elixir: number;
  card_count: number;
}

/**
 * Complete deck details with all cards
 */
export interface Deck extends DeckListItem {
  cards: Card[];
  created_at: string;
  updated_at?: string;
}

/**
 * Statistics for a specific deck matchup
 */
export interface MatchupStats {
  opponent_deck_id: number;
  opponent_deck_name: string;
  opponent_archetype: string;
  winrate: number;
  sample_size: number;
  top_1000_winrate: number;
  last_updated: string;
}

/**
 * Complete statistics for a deck including all matchups
 */
export interface DeckStats {
  deck: Deck;
  matchups: MatchupStats[];
  global_winrate: number;
  meta_share: number;
}

/* ============================================
   BATTLE LOG MODELS
   ============================================ */

export interface BattleCard {
  id: number;
  name: string;
  elixir_cost: number | null;
  rarity: string | null;
  level: number | null;
  icon_url: string | null;
}

export interface Battle {
  id: number;
  battle_key: string;
  battle_time: string;
  battle_type: string | null;
  game_mode_name: string | null;
  arena_name: string | null;
  team1_tag: string;
  team1_name: string | null;
  team1_crowns: number | null;
  team1_starting_trophies: number | null;
  team1_trophy_change: number | null;
  team1_cards: BattleCard[];
  team2_tag: string;
  team2_name: string | null;
  team2_crowns: number | null;
  team2_starting_trophies: number | null;
  team2_trophy_change: number | null;
  team2_cards: BattleCard[];
  winner_tag: string | null;
}

export interface BattleListResponse {
  items: Battle[];
  total: number;
  offset: number;
  limit: number;
}

/**
 * Card returned by the /api/v1/cards endpoint.
 * `type` can be null for cards whose type was not stored at sync time.
 */
export interface CardApiItem extends Omit<Card, 'type'> {
  type?: 'troop' | 'spell' | 'building' | null;
  description?: string;
}

/* ============================================
   ORACLE MODELS
   ============================================ */

/**
 * Category classification for Oracle advice
 */
export interface OracleAdviceCategory {
  name: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
}

/**
 * Single tactical advice from the Oracle
 */
export interface OracleAdvice {
  id: string;
  category: OracleAdviceCategory;
  title: string;
  description: string;
  cards_involved: string[];
  timing?: string;
}

/**
 * Difficulty rating for a matchup
 */
export type MatchupDifficulty = 'favorable' | 'even' | 'unfavorable' | 'hard';

/**
 * Source of Oracle advice
 */
export type OracleSource = 'cached' | 'llm' | 'mock';

/**
 * Complete Oracle analysis for a matchup
 */
export interface OracleMatchup {
  player_deck: Deck;
  opponent_deck: Deck;
  winrate_prediction: number;
  difficulty: MatchupDifficulty;
  advice: OracleAdvice[];
  generated_at: string;
  source: OracleSource;
}

/**
 * Request parameters for Oracle analysis
 */
export interface OracleRequest {
  player_deck_id: number;
  opponent_deck_id: number;
  force_refresh?: boolean;
}

/* ============================================
   PLAYER MODELS
   ============================================ */

/**
 * A single card inside a player's current deck (from /api/v1/players/:tag)
 */
export interface PlayerCardItem {
  id: number | null;
  name: string;
  elixir_cost: number | null;
  rarity: string | null;
  level: number | null;
  icon_url: string | null;
}

/**
 * Full player profile returned by GET /api/v1/players/:tag
 */
export interface PlayerProfile {
  tag: string;
  name: string | null;
  trophies: number | null;
  best_trophies: number | null;
  exp_level: number | null;
  wins: number | null;
  losses: number | null;
  battle_count: number | null;
  league_number: number | null;
  league_rank: number | null;
  season: string | null;
  current_deck: PlayerCardItem[];
}

/**
 * Lightweight player entry for leaderboard list views
 */
export interface PlayerListItem {
  tag: string;
  name: string | null;
  trophies: number | null;
  best_trophies: number | null;
  league_number: number | null;
  league_rank: number | null;
  season: string | null;
}

/**
 * Paginated list of players returned by GET /api/v1/players
 */
export interface PlayerListResponse {
  items: PlayerListItem[];
  total: number;
  offset: number;
  limit: number;
}

/**
 * Response after importing a player deck (legacy, kept for compatibility)
 */
export interface PlayerImportResponse {
  player: PlayerProfile;
  deck?: Deck;
  message: string;
}


/* ============================================
   API RESPONSE WRAPPERS
   ============================================ */

/**
 * Standard paginated response
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Standard error response
 */
export interface ErrorResponse {
  error: string;
  message: string;
  detail?: string;
}
