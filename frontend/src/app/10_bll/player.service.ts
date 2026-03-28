import { Injectable, computed, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { PlayerDal } from '../00_dal/player.dal';
import { LoadingState } from '../01_models/app.model';
import { BattleItem, PlayerDetail, PlayerListItem, PlayerSearchResponse } from '../01_models/player.model';

@Injectable({ providedIn: 'root' })
export class PlayerService {
  private dal = inject(PlayerDal);

  private static readonly PLAYER_CACHE_MS = 3 * 60 * 1000;
  private static readonly LS_KEY_PREFIX = 'crtracker_player_lastReload_';

  // ── State signals ──────────────────────────────────────────────────────────
  topPlayers = signal<PlayerListItem[]>([]);
  topTotal = signal<number>(0);
  searchResults = signal<PlayerSearchResponse | null>(null);
  selectedPlayer = signal<PlayerDetail | null>(null);
  battles = signal<BattleItem[]>([]);

  topLoadingState = signal<LoadingState>('idle');
  searchLoadingState = signal<LoadingState>('idle');
  playerLoadingState = signal<LoadingState>('idle');
  battlesLoadingState = signal<LoadingState>('idle');
  error = signal<string | null>(null);

  private _selectedPlayerTag: string | null = null;

  private getLastReloadAt(tag: string): number | null {
    const stored = localStorage.getItem(PlayerService.LS_KEY_PREFIX + tag);
    return stored ? parseInt(stored, 10) : null;
  }

  private setLastReloadAt(tag: string): void {
    localStorage.setItem(PlayerService.LS_KEY_PREFIX + tag, Date.now().toString());
  }

  // ── Derived ────────────────────────────────────────────────────────────────
  isLoadingTop = computed(() => this.topLoadingState() === 'loading');
  isSearching = computed(() => this.searchLoadingState() === 'loading');
  isLoadingPlayer = computed(() => this.playerLoadingState() === 'loading');
  isLoadingBattles = computed(() => this.battlesLoadingState() === 'loading');
  hasTopError = computed(() => this.topLoadingState() === 'error');
  hasSearchError = computed(() => this.searchLoadingState() === 'error');
  hasPlayerError = computed(() => this.playerLoadingState() === 'error');
  hasBattlesError = computed(() => this.battlesLoadingState() === 'error');

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
    const lastReload = this.getLastReloadAt(tag);
    const isFresh = lastReload != null && (now - lastReload) < PlayerService.PLAYER_CACHE_MS;

    if (isFresh && this._selectedPlayerTag === tag && this.selectedPlayer() != null) {
      return;
    }

    this.playerLoadingState.set('loading');
    this.error.set(null);
    try {
      const player = await firstValueFrom(this.dal.getPlayer(tag));
      this.selectedPlayer.set(player);
      this._selectedPlayerTag = tag;
      this.setLastReloadAt(tag);
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

  async loadBattles(tag: string): Promise<void> {
    this.battlesLoadingState.set('loading');
    try {
      const response = await firstValueFrom(this.dal.getBattles(tag));
      this.battles.set(response.battles);
      this.battlesLoadingState.set('success');
    } catch {
      this.battlesLoadingState.set('error');
    }
  }
}
