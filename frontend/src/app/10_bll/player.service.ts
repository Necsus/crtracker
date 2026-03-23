import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { PlayerDal } from '../00_dal/player.dal';
import { LoadingState } from '../01_models/app.model';
import { PlayerDetail, PlayerListItem, PlayerSearchResponse } from '../01_models/player.model';

@Injectable({ providedIn: 'root' })
export class PlayerService {
  private dal = inject(PlayerDal);

  private static readonly PLAYER_CACHE_MS = 5 * 60 * 1000;

  // ── State signals ──────────────────────────────────────────────────────────
  topPlayers = signal<PlayerListItem[]>([]);
  topTotal = signal<number>(0);
  searchResults = signal<PlayerSearchResponse | null>(null);
  selectedPlayer = signal<PlayerDetail | null>(null);

  topLoadingState = signal<LoadingState>('idle');
  searchLoadingState = signal<LoadingState>('idle');
  playerLoadingState = signal<LoadingState>('idle');
  error = signal<string | null>(null);

  private _selectedPlayerTag: string | null = null;
  private _selectedPlayerLoadedAt: number | null = null;

  // ── Derived ────────────────────────────────────────────────────────────────
  isLoadingTop = computed(() => this.topLoadingState() === 'loading');
  isSearching = computed(() => this.searchLoadingState() === 'loading');
  isLoadingPlayer = computed(() => this.playerLoadingState() === 'loading');
  hasTopError = computed(() => this.topLoadingState() === 'error');
  hasSearchError = computed(() => this.searchLoadingState() === 'error');
  hasPlayerError = computed(() => this.playerLoadingState() === 'error');

  // ── Actions ────────────────────────────────────────────────────────────────

  async loadTopPlayers(page = 1, pageSize = 20): Promise<void> {
    this.topLoadingState.set('loading');
    this.error.set(null);
    try {
      const response = await firstValueFrom(this.dal.listTop(page, pageSize));
      this.topPlayers.set(response.items);
      this.topTotal.set(response.total);
      this.topLoadingState.set('success');
    } catch {
      this.error.set('Impossible de charger les joueurs.');
      this.topLoadingState.set('error');
    }
  }

  async search(query: string): Promise<void> {
    if (!query.trim()) {
      this.clearSearch();
      return;
    }
    this.searchLoadingState.set('loading');
    this.error.set(null);
    try {
      const response = await firstValueFrom(this.dal.search(query));
      this.searchResults.set(response);
      this.searchLoadingState.set('success');
    } catch {
      this.error.set('Recherche échouée. Vérifiez votre connexion.');
      this.searchLoadingState.set('error');
    }
  }

  async loadPlayer(tag: string): Promise<void> {
    const now = Date.now();
    const isSameTag = this._selectedPlayerTag === tag;
    const isFresh = this._selectedPlayerLoadedAt != null
      && (now - this._selectedPlayerLoadedAt) < PlayerService.PLAYER_CACHE_MS;

    if (isSameTag && isFresh && this.selectedPlayer() != null) {
      return;
    }

    this.playerLoadingState.set('loading');
    this.error.set(null);
    try {
      const player = await firstValueFrom(this.dal.getPlayer(tag));
      this.selectedPlayer.set(player);
      this._selectedPlayerTag = tag;
      this._selectedPlayerLoadedAt = Date.now();
      this.playerLoadingState.set('success');
    } catch {
      this.error.set('Joueur introuvable.');
      this.playerLoadingState.set('error');
    }
  }

  clearSearch(): void {
    this.searchResults.set(null);
    this.searchLoadingState.set('idle');
  }
}
