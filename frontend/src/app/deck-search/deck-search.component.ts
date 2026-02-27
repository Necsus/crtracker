/* ============================================
   DECK SEARCH FEATURE COMPONENT
   Search interface and deck statistics dashboard
   ============================================ */

import { Component, inject, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

import { DeckService } from '../10_bll/deck.service';
import { DeckDisplayComponent } from '../shared/components/deck-display/deck-display.component';
import { MatchupCardComponent } from '../shared/components/matchup-card/matchup-card.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';
import { WinrateBadgeComponent } from '../shared/components/winrate-badge/winrate-badge.component';

/** Regex for valid Clash Royale player tag */
const PLAYER_TAG_REGEX = /^#?[0289PYLQGRJCUV]{3,12}$/i;

/**
 * Deck Search Component - Smart component
 *
 * Features:
 * - Search decks by archetype or name (debounced)
 * - Import deck by player tag (validated)
 * - Display deck statistics and matchups
 * - Navigate to Oracle detail view
 */
@Component({
  selector: 'app-deck-search',
  standalone: true,
  imports: [
    DeckDisplayComponent,
    MatchupCardComponent,
    LoadingSpinnerComponent,
    WinrateBadgeComponent,
  ],
  templateUrl: './deck-search.component.html',
  styleUrl: './deck-search.component.scss',
})
export class DeckSearchComponent implements OnInit, OnDestroy {
  private readonly deckService = inject(DeckService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();
  private readonly searchSubject$ = new Subject<string>();

  @ViewChild('deckDetailsSection') deckDetailsSection?: ElementRef<HTMLElement>;

  /* ============================================
     SIGNALS (READ-ONLY FROM SERVICE)
     ============================================ */

  readonly isLoading = this.deckService.isLoading;
  readonly hasError = this.deckService.hasError;
  readonly errorMessage = this.deckService.errorMessage;
  readonly filteredDecks = this.deckService.filteredDecks;
  readonly currentDeck = this.deckService.currentDeck;
  readonly currentDeckStats = this.deckService.currentDeckStats;
  readonly featuredDecks = this.deckService.featuredDecks;

  /* ============================================
     LOCAL STATE
     ============================================ */

  searchQuery = '';
  playerTag = '';
  playerTagError = '';
  showImportModal = false;

  /* ============================================
     LIFECYCLE
     ============================================ */

  ngOnInit(): void {
    // Load initial data
    this.deckService.loadPopularDecks(8);
    this.deckService.loadDecks(0, 50);

    // Setup debounced search (300ms)
    this.searchSubject$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$),
    ).subscribe(query => {
      if (query.length >= 2) {
        this.deckService.searchDecks(query);
      } else if (query.length === 0) {
        this.deckService.loadDecks(0, 50);
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /* ============================================
     SEARCH & IMPORT
     ============================================ */

  onSearchInput(query: string): void {
    this.searchQuery = query;
    this.searchSubject$.next(query);
  }

  onImportPlayer(): void {
    const tag = this.playerTag.trim();
    if (!tag) {
      this.playerTagError = 'Please enter a player tag.';
      return;
    }
    if (!PLAYER_TAG_REGEX.test(tag)) {
      this.playerTagError = 'Invalid tag format. Example: #ABC123DE';
      return;
    }
    this.playerTagError = '';
    this.deckService.importPlayerDeck(tag);
    this.showImportModal = false;
  }

  /* ============================================
     DECK SELECTION
     ============================================ */

  onSelectDeck(deckId: number): void {
    this.deckService.selectDeckWithStats(deckId);

    // Scroll to deck details on mobile
    if (window.innerWidth < 768) {
      setTimeout(() => {
        this.deckDetailsSection?.nativeElement.scrollIntoView({
          behavior: 'smooth',
        });
      }, 100);
    }
  }

  onViewMatchup(playerDeckId: number, opponentDeckId: number): void {
    this.router.navigate(['/oracle', playerDeckId, opponentDeckId]);
  }

  /* ============================================
     ERROR HANDLING
     ============================================ */

  onDismissError(): void {
    this.deckService.clearError();
  }

  onClearSelection(): void {
    this.deckService.clearSelection();
  }
}
