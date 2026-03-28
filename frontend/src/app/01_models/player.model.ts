export interface PlayerListItem {
  tag: string;
  name: string;
  exp_level: number;
  trophies: number;
  best_trophies: number;
  wins: number;
  losses: number;
  battle_count: number;
  winrate: number | null;
  clan_tag: string | null;
  clan_name: string | null;
  arena_id: number | null;
  arena_name: string | null;
  pol_league_number: number | null;
  pol_trophies: number | null;
  pol_rank: number | null;
  last_synced_at: string;
}

export interface PlayerDetail extends PlayerListItem {
  three_crown_wins: number;
  challenge_max_wins: number | null;
  total_donations: number | null;
  donations: number | null;
  war_day_wins: number | null;
  clan_badge_id: number | null;
  role: string | null;
  current_deck: CardItem[] | null;
  current_favourite_card: CardItem | null;
  league_statistics: LeagueStatistics | null;
  badges: BadgeItem[] | null;
  created_at: string;
}

export interface CardItem {
  name: string;
  id: number;
  level?: number;
  maxLevel?: number;
  starLevel?: number;
  evolutionLevel?: number;
  iconUrls?: { medium?: string; evolutionMedium?: string; heroMedium?: string };
}

export interface LeagueStatistics {
  currentSeason?: { trophies?: number; bestTrophies?: number; rank?: number };
  previousSeason?: { id?: string; trophies?: number; bestTrophies?: number; rank?: number };
  bestSeason?: { id?: string; trophies?: number; rank?: number };
}

export interface BadgeItem {
  name: string;
  level?: number;
  maxLevel?: number;
  progress?: number;
  target?: number;
  iconUrls?: { large?: string };
}

export interface BattleCardItem {
  name: string;
  id: number;
  level?: number;
  maxLevel?: number;
  iconUrls?: { medium?: string };
}

export interface BattleItem {
  id: number;
  battle_time: string;
  battle_type: string | null;
  game_mode_name: string | null;
  arena_name: string | null;
  result: 'win' | 'loss' | 'draw';
  trophy_change: number | null;
  player_crowns: number;
  opponent_tag: string | null;
  opponent_name: string | null;
  opponent_crowns: number;
  opponent_trophies: number | null;
  player_cards: BattleCardItem[] | null;
  opponent_cards: BattleCardItem[] | null;
}

export interface BattleListResponse {
  battles: BattleItem[];
  total: number;
}

export interface PlayerSearchResponse {
  players: PlayerListItem[];
  source: 'db' | 'api';
  total: number;
}

export interface PlayerTopResponse {
  total: number;
  page: number;
  page_size: number;
  items: PlayerListItem[];
}
