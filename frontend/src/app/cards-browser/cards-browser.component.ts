/* ============================================
   CARDS BROWSER COMPONENT
   Displays the full CR card catalogue with filters
   ============================================ */

import { NgClass } from '@angular/common';
import {
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { DeckDal } from '../00_dal/deck.dal';
import type { Card, CardApiItem } from '../01_models/deck.model';
import { CardIconComponent } from '../shared/components/card-icon/card-icon.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

type RarityFilter = 'all' | 'common' | 'rare' | 'epic' | 'legendary' | 'champion';
type TypeFilter = 'all' | 'troop' | 'spell' | 'building';

@Component({
  selector: 'app-cards-browser',
  standalone: true,
  imports: [FormsModule, NgClass, CardIconComponent, LoadingSpinnerComponent],
  templateUrl: './cards-browser.component.html',
  styleUrl: './cards-browser.component.scss',
})
export class CardsBrowserComponent implements OnInit {
  private readonly dal = inject(DeckDal);

  /* ── State ─────────────────────────────────────── */
  readonly allCards = signal<CardApiItem[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly searchQuery = signal('');
  readonly rarityFilter = signal<RarityFilter>('all');
  readonly typeFilter = signal<TypeFilter>('all');

  /* ── Static filter options ──────────────────────── */
  readonly rarities: { value: RarityFilter; label: string; emoji: string }[] = [
    { value: 'all', label: 'All', emoji: '✨' },
    { value: 'common', label: 'Common', emoji: '⚪' },
    { value: 'rare', label: 'Rare', emoji: '🟠' },
    { value: 'epic', label: 'Epic', emoji: '🟣' },
    { value: 'legendary', label: 'Legendary', emoji: '🌟' },
    { value: 'champion', label: 'Champion', emoji: '👑' },
  ];

  readonly types: { value: TypeFilter; label: string; emoji: string }[] = [
    { value: 'all', label: 'All', emoji: '🎴' },
    { value: 'troop', label: 'Troop', emoji: '⚔️' },
    { value: 'spell', label: 'Spell', emoji: '🔮' },
    { value: 'building', label: 'Building', emoji: '🏰' },
  ];

  /* ── Derived filtered list ──────────────────────── */
  readonly filteredCards = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const rarity = this.rarityFilter();
    const type = this.typeFilter();

    return this.allCards().filter(card => {
      if (q && !card.name.toLowerCase().includes(q)) return false;
      if (rarity !== 'all' && card.rarity !== rarity) return false;
      if (type !== 'all' && card.type !== type) return false;
      return true;
    });
  });

  /** Normalises null type → undefined so CardIconComponent's strict input is satisfied. */
  readonly displayCards = computed<Card[]>(() =>
    this.filteredCards().map(c => ({ ...c, type: c.type ?? undefined }))
  );

  readonly totalCount = computed(() => this.allCards().length);
  readonly filteredCount = computed(() => this.filteredCards().length);

  /* ── Lifecycle ──────────────────────────────────── */
  ngOnInit(): void {
    this.dal.listCards({ limit: 500 }).subscribe({
      next: cards => {
        this.allCards.set(cards);
        this.loading.set(false);
      },
      error: err => {
        this.error.set('Failed to load cards. Please try again.');
        this.loading.set(false);
        console.error('[CardsBrowser] load error', err);
      },
    });
  }

  /* ── Event handlers ─────────────────────────────── */
  setRarity(rarity: RarityFilter): void {
    this.rarityFilter.set(rarity);
  }

  setType(type: TypeFilter): void {
    this.typeFilter.set(type);
  }

  onSearch(value: string): void {
    this.searchQuery.set(value);
  }

  clearFilters(): void {
    this.searchQuery.set('');
    this.rarityFilter.set('all');
    this.typeFilter.set('all');
  }
}
