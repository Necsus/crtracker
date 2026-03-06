/* ============================================
   BATTLES LOG COMPONENT
   Displays battle history from the top 1000 Path of Legend players
   ============================================ */

import { DatePipe, DecimalPipe, NgClass } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { DeckDal } from '../00_dal/deck.dal';
import type { Battle } from '../01_models/deck.model';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

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
  selector: 'app-battles-log',
  standalone: true,
  imports: [NgClass, DatePipe, LoadingSpinnerComponent, DecimalPipe, RouterLink],
  templateUrl: './battles-log.component.html',
})
export class BattlesLogComponent implements OnInit {
  private readonly dal = inject(DeckDal);

  /* ── State ──────────────────────────────────── */
  readonly battles = signal<Battle[]>([]);
  readonly total = signal(0);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly availableTypes = signal<string[]>([]);

  readonly typeFilter = signal<string>('all');
  readonly offset = signal(0);
  readonly limit = 20;

  /* ── Derived ────────────────────────────────── */
  readonly totalPages = computed(() => Math.ceil(this.total() / this.limit));
  readonly currentPage = computed(() => Math.floor(this.offset() / this.limit) + 1);
  readonly hasNext = computed(() => this.offset() + this.limit < this.total());
  readonly hasPrev = computed(() => this.offset() > 0);

  ngOnInit(): void {
    this.dal.listBattleTypes().subscribe({
      next: (types) => this.availableTypes.set(types),
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    const params: Record<string, unknown> = { offset: this.offset(), limit: this.limit };
    if (this.typeFilter() !== 'all') params['battle_type'] = this.typeFilter();

    this.dal.listBattles(params as Parameters<DeckDal['listBattles']>[0]).subscribe({
      next: (res) => {
        this.battles.set(res.items);
        this.total.set(res.total);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Failed to load battles.');
        this.loading.set(false);
      },
    });
  }

  setType(t: string): void {
    this.typeFilter.set(t);
    this.offset.set(0);
    this.load();
  }

  nextPage(): void {
    if (!this.hasNext()) return;
    this.offset.update(o => o + this.limit);
    this.load();
  }

  prevPage(): void {
    if (!this.hasPrev()) return;
    this.offset.update(o => Math.max(0, o - this.limit));
    this.load();
  }

  /* ── Display helpers ────────────────────────── */
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
}
