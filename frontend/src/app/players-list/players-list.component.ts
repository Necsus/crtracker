/* ============================================
   PLAYERS LIST COMPONENT
   Path of Legend leaderboard page
   ============================================ */

import { DecimalPipe, NgClass } from '@angular/common';
import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';

import { DeckDal } from '../00_dal/deck.dal';
import type { PlayerListItem } from '../01_models/deck.model';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-players-list',
  standalone: true,
  imports: [NgClass, RouterLink, LoadingSpinnerComponent, DecimalPipe],
  templateUrl: './players-list.component.html',
})
export class PlayersListComponent implements OnInit, OnDestroy {
  private readonly dal = inject(DeckDal);
  private readonly searchInput$ = new Subject<string>();

  /* ── State ──────────────────────────────────── */
  readonly players = signal<PlayerListItem[]>([]);
  readonly total = signal(0);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly availableSeasons = signal<string[]>([]);

  readonly seasonFilter = signal<string | null>(null);
  readonly offset = signal(0);
  readonly limit = 50;

  /* ── Search state ───────────────────────────── */
  readonly searchQuery = signal('');
  readonly searchResults = signal<PlayerListItem[]>([]);
  readonly searchLoading = signal(false);
  readonly searchError = signal<string | null>(null);
  readonly isSearchMode = computed(() => this.searchQuery().trim().length > 0);

  /* ── Derived ────────────────────────────────── */
  readonly totalPages = computed(() => Math.ceil(this.total() / this.limit));
  readonly currentPage = computed(() => Math.floor(this.offset() / this.limit) + 1);
  readonly hasNext = computed(() => this.offset() + this.limit < this.total());
  readonly hasPrev = computed(() => this.offset() > 0);

  ngOnInit(): void {
    this.dal.listPlayerSeasons().subscribe({
      next: (seasons) => this.availableSeasons.set(seasons),
    });
    this.load();

    this.searchInput$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((q) => {
        if (!q.trim()) {
          this.searchResults.set([]);
          this.searchLoading.set(false);
          return [];
        }
        this.searchLoading.set(true);
        this.searchError.set(null);
        return this.dal.searchPlayers(q);
      }),
    ).subscribe({
      next: (results) => {
        this.searchResults.set(results);
        this.searchLoading.set(false);
      },
      error: () => {
        this.searchError.set('Search failed. Try again.');
        this.searchLoading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.searchInput$.complete();
  }

  onSearchInput(value: string): void {
    this.searchQuery.set(value);
    this.searchInput$.next(value);
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);

    const params: Record<string, unknown> = { offset: this.offset(), limit: this.limit };
    if (this.seasonFilter()) params['season'] = this.seasonFilter();

    this.dal.listPlayers(params as Parameters<DeckDal['listPlayers']>[0]).subscribe({
      next: (res) => {
        this.players.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load players.');
        this.loading.set(false);
      },
    });
  }

  setSeason(season: string | null): void {
    this.seasonFilter.set(season);
    this.offset.set(0);
    this.load();
  }

  nextPage(): void {
    this.offset.update((v) => v + this.limit);
    this.load();
  }

  prevPage(): void {
    this.offset.update((v) => Math.max(0, v - this.limit));
    this.load();
  }

  /* ── Helpers ─────────────────────────────────── */

  rankEmoji(rank: number | null): string {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank != null ? `#${rank}` : '—';
  }
}

