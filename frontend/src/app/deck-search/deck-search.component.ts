/* ============================================
   DECK SEARCH FEATURE COMPONENT
   Search interface — navigates to /decks/:id for full detail
   ============================================ */

import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

import { DeckService } from '../10_bll/deck.service';
import { CardIconComponent } from '../shared/components/card-icon/card-icon.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

/** Regex for valid Clash Royale player tag */
const PLAYER_TAG_REGEX = /^#?[0289PYLQGRJCUV]{3,12}$/i;

@Component({
  selector: 'app-deck-search',
  standalone: true,
  imports: [LoadingSpinnerComponent, CardIconComponent],
  templateUrl: './deck-search.component.html',
})
export class DeckSearchComponent implements OnInit, OnDestroy {
  private readonly deckService = inject(DeckService);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();
  private readonly searchSubject$ = new Subject<string>();

  /* ============================================
     SIGNALS (READ-ONLY FROM SERVICE)
     ============================================ */

  readonly isLoading = this.deckService.isLoading;
  readonly hasError = this.deckService.hasError;
  readonly errorMessage = this.deckService.errorMessage;
  readonly filteredDecks = this.deckService.filteredDecks;
  readonly featuredDecks = this.deckService.featuredDecks;

  /* ============================================
     LOCAL STATE
     ============================================ */

  searchQuery = '';
  playerTag = '';
  playerTagError = '';
  showImportModal = false;
  importLoading = false;

  /* ============================================
     LIFECYCLE
     ============================================ */

  ngOnInit(): void {
    this.deckService.loadPopularDecks(8);
    this.deckService.loadDecks(0, 50);

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
    this.importLoading = true;

    this.deckService.importPlayerDeck(tag).subscribe(response => {
      this.importLoading = false;
      this.showImportModal = false;
      if (response?.deck) {
        this.router.navigate(['/decks', response.deck.id]);
      }
    });
  }

  /* ============================================
     NAVIGATION
     ============================================ */

  onSelectDeck(deckId: number): void {
    this.router.navigate(['/decks', deckId]);
  }

  /* ============================================
     ERROR HANDLING
     ============================================ */

  onDismissError(): void {
    this.deckService.clearError();
  }
}
