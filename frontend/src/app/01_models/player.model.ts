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
  iconUrls?: { medium?: string };
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
