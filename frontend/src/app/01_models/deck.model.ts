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
  type: 'troop' | 'spell' | 'building';
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
 * Clash Royale player profile
 */
export interface PlayerProfile {
  tag: string;
  name: string;
  trophies: number;
  best_trophies: number;
  arena: string;
  wins: number;
  losses: number;
  current_deck?: Card[];
}

/**
 * Response after importing a player deck
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
