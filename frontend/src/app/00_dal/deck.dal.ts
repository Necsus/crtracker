/* ============================================
   DECK DATA ACCESS LAYER
   All HTTP requests for deck-related operations
   ============================================ */

import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import type {
  Deck,
  DeckListItem,
  DeckStats,
  PlayerImportResponse,
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
}
