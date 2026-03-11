/* ============================================
   DECK BUSINESS LOGIC LAYER
   State management for deck operations using Signals
   ============================================ */

import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, Observable, of, switchMap, tap } from 'rxjs';

import { DeckDal } from '../00_dal/deck.dal';
import type { LoadingState } from '../01_models/app.model';
import type { Deck, DeckListItem, DeckStats, PlayerImportResponse } from '../01_models/deck.model';

/**
 * Deck Service - Manages deck state and operations
 *
 * Responsibilities:
 * - Fetch and cache deck lists and details
 * - Manage loading/error states
 * - Provide reactive state via computed signals
 */
@Injectable({ providedIn: 'root' })
export class DeckService {
  private readonly deckDal = inject(DeckDal);

  /* ============================================
     STATE SIGNALS
     ============================================ */

  /** Loading state for current operation */
  private readonly loadingState = signal<LoadingState>('idle');

  /** Current error message if any */
  private readonly error = signal<string | null>(null);

  /** All loaded decks list */
  private readonly decks = signal<DeckListItem[]>([]);

  /** Currently selected deck details */
  private readonly selectedDeck = signal<Deck | null>(null);

  /** Currently selected deck statistics */
  private readonly selectedDeckStats = signal<DeckStats | null>(null);

  /** Search query */
  private readonly searchQuery = signal('');

  /** Popular decks cache */
  private readonly popularDecks = signal<DeckListItem[]>([]);

  /* ============================================
     COMPUTED SIGNALS (READ-ONLY)
     ============================================ */

  /** Whether a loading operation is in progress */
  readonly isLoading = computed(() => this.loadingState() === 'loading');

  /** Whether there's an error */
  readonly hasError = computed(() => this.error() !== null);

  /** The error message */
  readonly errorMessage = computed(() => this.error());

  /** Filtered decks based on search query */
  readonly filteredDecks = computed(() => {
    const query = this.searchQuery().toLowerCase().trim();
    const allDecks = this.decks();

    if (!query) {
      return allDecks;
    }

    return allDecks.filter(deck =>
      deck.name.toLowerCase().includes(query) ||
      deck.archetype.toLowerCase().includes(query)
    );
  });

  /** Selected deck as readonly signal */
  readonly currentDeck = computed(() => this.selectedDeck());

  /** Selected deck stats as readonly signal */
  readonly currentDeckStats = computed(() => this.selectedDeckStats());

  /** Popular decks as readonly signal */
  readonly featuredDecks = computed(() => this.popularDecks());

  /* ============================================
     OPERATIONS
     ============================================ */

  /**
   * Load all decks with pagination
   */
  loadDecks(offset = 0, limit = 50): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.deckDal.listDecks(offset, limit).pipe(
      tap(decks => {
        this.decks.set(decks);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load decks');
        return of([]);
      })
    ).subscribe();
  }

  /**
   * Search decks by query
   */
  searchDecks(query: string): void {
    this.searchQuery.set(query);

    if (query.length >= 2) {
      this.loadingState.set('loading');
      this.deckDal.searchDecks(query, 0, 50).pipe(
        tap(decks => {
          this.decks.set(decks);
          this.loadingState.set('success');
        }),
        catchError(err => {
          this.loadingState.set('error');
          this.error.set(err.userMessage || 'Search failed');
          return of([]);
        })
      ).subscribe();
    }
  }

  /**
   * Load popular decks
   */
  loadPopularDecks(limit = 10): void {
    this.deckDal.getPopularDecks(limit).pipe(
      tap(decks => {
        this.popularDecks.set(decks);
      }),
      catchError(() => of([]))
    ).subscribe();
  }

  /**
   * Select a deck and load its full details
   */
  selectDeck(deckId: number): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.deckDal.getDeck(deckId).pipe(
      tap(deck => {
        this.selectedDeck.set(deck);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load deck details');
        return of(null);
      })
    ).subscribe();
  }

  /**
   * Load statistics for the selected deck
   */
  loadDeckStats(deckId: number): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.deckDal.getDeckStats(deckId).pipe(
      tap(stats => {
        this.selectedDeckStats.set(stats);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load deck statistics');
        return of(null);
      })
    ).subscribe();
  }

  /**
   * Select a deck and load both details and stats
   */
  selectDeckWithStats(deckId: number): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.deckDal.getDeck(deckId).pipe(
      tap(deck => this.selectedDeck.set(deck)),
      switchMap(deck => {
        if (!deck) {
          return of(null);
        }
        return this.deckDal.getDeckStats(deckId);
      }),
      tap(stats => {
        this.selectedDeckStats.set(stats);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load deck');
        return of(null);
      })
    ).subscribe();
  }

  /**
   * Import a deck from player tag
   * Returns an Observable so callers can react (e.g. navigate) after import.
   */
  importPlayerDeck(playerTag: string): Observable<PlayerImportResponse | null> {
    this.loadingState.set('loading');
    this.error.set(null);

    return this.deckDal.importPlayerDeck(playerTag).pipe(
      tap(response => {
        if (response.deck) {
          this.loadingState.set('success');
        } else {
          this.error.set(response.message);
          this.loadingState.set('error');
        }
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to import player deck');
        return of(null);
      })
    );
  }

  /* ============================================
     UTILITIES
     ============================================ */

  /**
   * Clear the current selection
   */
  clearSelection(): void {
    this.selectedDeck.set(null);
    this.selectedDeckStats.set(null);
  }

  /**
   * Clear the current error
   */
  clearError(): void {
    this.error.set(null);
  }

  /**
   * Get deck by ID from the list
   */
  getDeckById(deckId: number): DeckListItem | undefined {
    return this.decks().find(d => d.id === deckId);
  }
}
