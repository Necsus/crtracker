/* ============================================
   DECK DATA ACCESS LAYER
   All HTTP requests for deck-related operations
   ============================================ */

import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import type {
  BattleListResponse,
  CardApiItem,
  Deck,
  DeckListItem,
  DeckStats,
  PlayerImportResponse,
  PlayerListResponse,
  PlayerProfile,
} from '../01_models/deck.model';
import { buildUrl } from './api.interceptor';

/**
 * Deck DAL - Handles all deck API calls
 *
 * This service makes HTTP requests to the backend and returns Observables.
 * It does NOT manage state - that's handled by the BLL.
 */
@Injectable({ providedIn: 'root' })
export class DeckDal {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/api/v1';

  /* ============================================
     DECK RETRIEVAL
     ============================================ */

  /**
   * Get a paginated list of all decks
   */
  listDecks(offset = 0, limit = 20): Observable<DeckListItem[]> {
    const url = buildUrl(`${this.basePath}/decks`, { offset, limit });
    return this.http.get<DeckListItem[]>(url);
  }

  /**
   * Search decks by name or archetype
   */
  searchDecks(query: string, offset = 0, limit = 20): Observable<DeckListItem[]> {
    const url = buildUrl(`${this.basePath}/decks/search`, { query, offset, limit });
    return this.http.get<DeckListItem[]>(url);
  }

  /**
   * Get popular decks by meta share
   */
  getPopularDecks(limit = 10): Observable<DeckListItem[]> {
    const url = buildUrl(`${this.basePath}/decks/popular`, { limit });
    return this.http.get<DeckListItem[]>(url);
  }

  /**
   * Get complete details for a specific deck
   */
  getDeck(deckId: number): Observable<Deck> {
    return this.http.get<Deck>(`${this.basePath}/deck/${deckId}`);
  }

  /**
   * Get complete statistics for a deck including matchups
   */
  getDeckStats(deckId: number): Observable<DeckStats> {
    return this.http.get<DeckStats>(`${this.basePath}/deck/${deckId}/stats`);
  }

  /* ============================================
     PLAYER IMPORT
     ============================================ */

  /**
   * Import a deck from a player profile using player tag
   */
  importPlayerDeck(playerTag: string): Observable<PlayerImportResponse> {
    const url = buildUrl(`${this.basePath}/player/import`, {
      player_tag: playerTag,
    });
    return this.http.post<PlayerImportResponse>(url, {});
  }

  /* ============================================
     CARDS
     ============================================ */

  /**
   * List all cards, with optional rarity/type filters and name search
   */
  listCards(params: {
    rarity?: string;
    type?: string;
    q?: string;
    offset?: number;
    limit?: number;
  } = {}): Observable<CardApiItem[]> {
    const url = buildUrl(`${this.basePath}/cards`, params);
    return this.http.get<CardApiItem[]>(url);
  }

  /**
   * Get full details for a single card by its CR numeric ID
   */
  getCard(cardId: string): Observable<CardApiItem> {
    return this.http.get<CardApiItem>(`${this.basePath}/cards/${cardId}`);
  }

  /* ============================================
     BATTLES
     ============================================ */

  /**
   * List battles with optional type filter and pagination
   */
  listBattles(params: {
    battle_type?: string;
    offset?: number;
    limit?: number;
  } = {}): Observable<BattleListResponse> {
    const url = buildUrl(`${this.basePath}/battles`, params);
    return this.http.get<BattleListResponse>(url);
  }

  /**
   * List battles where the given deck was used by either team
   */
  listBattlesByDeck(deckId: number, offset = 0, limit = 20): Observable<BattleListResponse> {
    const url = buildUrl(`${this.basePath}/battles`, { deck_id: deckId, offset, limit });
    return this.http.get<BattleListResponse>(url);
  }

  /**
   * List all available battle types
   */
  listBattleTypes(): Observable<string[]> {
    return this.http.get<string[]>(`${this.basePath}/battles/types`);
  }

  /* ============================================
     PLAYERS
     ============================================ */

  /**
   * Get leaderboard list of players (paginated, ordered by league_rank)
   */
  listPlayers(params: { season?: string; offset?: number; limit?: number } = {}): Observable<PlayerListResponse> {
    const url = buildUrl(`${this.basePath}/players`, params);
    return this.http.get<PlayerListResponse>(url);
  }

  /**
   * Get available seasons stored in the players table
   */
  listPlayerSeasons(): Observable<string[]> {
    return this.http.get<string[]>(`${this.basePath}/players/seasons`);
  }

  /**
   * Get full player profile by battle tag (with or without leading #)
   */
  getPlayer(tag: string): Observable<PlayerProfile> {
    const encoded = encodeURIComponent(tag.replace(/^#/, ''));
    return this.http.get<PlayerProfile>(`${this.basePath}/players/${encoded}`);
  }
}
