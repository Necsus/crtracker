/* ============================================
   DECK DETAIL FEATURE COMPONENT
   Full page view for a single deck with stats and matchups.
   ============================================ */

import { DatePipe, NgClass } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { DeckDal } from '../00_dal/deck.dal';
import type { Battle, BattleCard, Card, Deck, DeckStats } from '../01_models/deck.model';
import { CardIconComponent } from '../shared/components/card-icon/card-icon.component';
import { DeckDisplayComponent } from '../shared/components/deck-display/deck-display.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';
import { MatchupCardComponent } from '../shared/components/matchup-card/matchup-card.component';
import { WinrateBadgeComponent } from '../shared/components/winrate-badge/winrate-badge.component';

const TYPE_META: Record<string, { label: string; emoji: string; color: string }> = {
  pathOfLegend: { label: 'Path of Legend', emoji: '⚔️', color: '#f6c237' },
  PvP: { label: 'Ladder', emoji: '🏆', color: '#40a0f0' },
  tournament: { label: 'Tournament', emoji: '🎯', color: '#a050c8' },
  clanMate: { label: 'Clan Mate', emoji: '🤝', color: '#40c080' },
  friendly: { label: 'Friendly', emoji: '😊', color: '#6080a8' },
  boatBattle: { label: 'Boat Battle', emoji: '⛵', color: '#4080c0' },
  riverRacePvP: { label: 'River Race', emoji: '🌊', color: '#209898' },
  riverRaceDuel: { label: 'Duel', emoji: '🗡️', color: '#c06040' },
  riverRaceDuelColosseum: { label: 'Colosseum', emoji: '🏛️', color: '#d0a030' },
  trail: { label: 'Trail', emoji: '🧪', color: '#8090c0' },
};

@Component({
  selector: 'app-deck-detail',
  standalone: true,
  imports: [RouterLink, NgClass, DatePipe, CardIconComponent, DeckDisplayComponent, LoadingSpinnerComponent, MatchupCardComponent, WinrateBadgeComponent],
  templateUrl: './deck-detail.component.html',
})
export class DeckDetailComponent implements OnInit {
  private readonly dal = inject(DeckDal);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly deck = signal<Deck | null>(null);
  readonly stats = signal<DeckStats | null>(null);
  readonly isLoading = signal(true);
  readonly statsLoading = signal(false);
  readonly error = signal<string | null>(null);

  /* ── Battle log state ───────────────────────── */
  readonly battles = signal<Battle[]>([]);
  readonly battlesTotal = signal(0);
  readonly battlesLoading = signal(false);
  readonly battlesOffset = signal(0);
  readonly battlesLimit = 20;

  readonly battlesPage = computed(() => Math.floor(this.battlesOffset() / this.battlesLimit) + 1);
  readonly battlesTotalPages = computed(() => Math.ceil(this.battlesTotal() / this.battlesLimit));
  readonly hasPrevBattles = computed(() => this.battlesOffset() > 0);
  readonly hasNextBattles = computed(() => this.battlesOffset() + this.battlesLimit < this.battlesTotal());

  readonly activeTab = signal<'stats' | 'battles'>('stats');
  setTab(tab: 'stats' | 'battles'): void { this.activeTab.set(tab); }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.router.navigate(['/']);
      return;
    }
    this.loadDeck(id);
    this.loadBattles(id, 0);
  }

  private loadDeck(id: number): void {
    this.isLoading.set(true);
    this.error.set(null);
    this.deck.set(null);
    this.stats.set(null);
    this.statsLoading.set(false);

    this.dal.getDeck(id).subscribe({
      next: (deck) => {
        this.deck.set(deck);
        this.isLoading.set(false);
        this.statsLoading.set(true);

        this.dal.getDeckStats(id).subscribe({
          next: (stats) => {
            this.stats.set(stats);
            this.statsLoading.set(false);
          },
          error: () => {
            this.statsLoading.set(false);
          },
        });
      },
      error: () => {
        this.error.set('Deck not found or failed to load.');
        this.isLoading.set(false);
      },
    });
  }

  private loadBattles(deckId: number, offset: number): void {
    this.battlesLoading.set(true);
    this.battlesOffset.set(offset);
    this.dal.listBattlesByDeck(deckId, offset, this.battlesLimit).subscribe({
      next: (res) => {
        this.battles.set(res.items);
        this.battlesTotal.set(res.total);
        this.battlesLoading.set(false);
      },
      error: () => this.battlesLoading.set(false),
    });
  }

  nextBattlesPage(): void {
    if (!this.hasNextBattles()) return;
    const id = this.deck()!.id;
    this.loadBattles(id, this.battlesOffset() + this.battlesLimit);
  }

  prevBattlesPage(): void {
    if (!this.hasPrevBattles()) return;
    const id = this.deck()!.id;
    this.loadBattles(id, Math.max(0, this.battlesOffset() - this.battlesLimit));
  }

  onViewMatchup(opponentDeckId: number): void {
    this.router.navigate(['/oracle', this.deck()!.id, opponentDeckId]);
  }

  /* ── Battle display helpers ─────────────────── */
  typeMeta(type: string | null) {
    return TYPE_META[type ?? ''] ?? { label: type ?? '?', emoji: '🎮', color: '#6080a8' };
  }

  trophyClass(change: number | null): string {
    if (change == null) return '';
    return change > 0 ? 'text-[#40d070]' : change < 0 ? 'text-[#d04040]' : 'text-[#6080a8]';
  }

  trophySign(change: number | null): string {
    if (change == null) return '';
    return change > 0 ? `+${change}` : `${change}`;
  }

  isWinner(battle: Battle, tag: string): boolean {
    return battle.winner_tag === tag;
  }

  /** Adapt a BattleCard to the Card interface for CardIconComponent. */
  toCard(bc: BattleCard): Card {
    const VALID_RARITIES = new Set(['common', 'rare', 'epic', 'legendary', 'champion']);
    const rarity = (bc.rarity ?? '').toLowerCase();
    return {
      id: String(bc.id),
      name: bc.name,
      elixir: bc.elixir_cost ?? 0,
      rarity: (VALID_RARITIES.has(rarity) ? rarity : 'common') as Card['rarity'],
      icon_url: bc.icon_url ?? undefined,
    };
  }
}
