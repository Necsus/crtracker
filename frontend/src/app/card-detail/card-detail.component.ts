/* ============================================
   CARD DETAIL COMPONENT
   Full info page for a single Clash Royale card
   ============================================ */

import { NgClass, TitleCasePipe } from '@angular/common';
import {
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { DeckDal } from '../00_dal/deck.dal';
import type { Card, CardApiItem, DeckListItem } from '../01_models/deck.model';
import { CardIconComponent } from '../shared/components/card-icon/card-icon.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';
import { WinrateBadgeComponent } from '../shared/components/winrate-badge/winrate-badge.component';

/* ── Mock data shape ────────────────────────── */
interface MockCardStats {
  usage_rate: number;
  win_rate_with: number;
  best_synergy: string;
  best_counter: string;
  avg_elixir_deck: number;
  top_archetype: string;
}

const MOCK_STATS: MockCardStats = {
  usage_rate: 18.4,
  win_rate_with: 52.3,
  best_synergy: 'Goblin Barrel',
  best_counter: 'Inferno Tower',
  avg_elixir_deck: 3.6,
  top_archetype: 'Beatdown',
};

const MOCK_DECKS: DeckListItem[] = [
  { id: 1, name: 'Classic Beatdown', archetype: 'Beatdown', avg_elixir: 3.6, card_count: 8 },
  { id: 2, name: 'Hog Cycle', archetype: 'Cycle', avg_elixir: 2.9, card_count: 8 },
  { id: 3, name: 'Giant Double Prince', archetype: 'Beatdown', avg_elixir: 4.0, card_count: 8 },
];

@Component({
  selector: 'app-card-detail',
  standalone: true,
  imports: [NgClass, RouterLink, CardIconComponent, LoadingSpinnerComponent, WinrateBadgeComponent, TitleCasePipe],
  templateUrl: './card-detail.component.html',
  styleUrl: './card-detail.component.scss',
})
export class CardDetailComponent implements OnInit {
  private readonly dal = inject(DeckDal);
  private readonly route = inject(ActivatedRoute);

  /* ── State ─────────────────────────────────── */
  readonly card = signal<CardApiItem | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  /* ── Mock data (until backend stats exist) ── */
  readonly mockStats = MOCK_STATS;
  readonly mockDecks = MOCK_DECKS;

  ngOnInit(): void {
    const cardId = this.route.snapshot.paramMap.get('id') ?? '';
    this.dal.getCard(cardId).subscribe({
      next: (c) => {
        this.card.set(c);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Card not found or failed to load.');
        this.loading.set(false);
      },
    });
  }

  /* ── Helpers ────────────────────────────────── */
  asCard(c: CardApiItem): Card {
    return { ...c, type: c.type ?? undefined };
  }

  rarityClass(rarity?: string): string {
    switch (rarity) {
      case 'common': return 'rarity-common';
      case 'rare': return 'rarity-rare';
      case 'epic': return 'rarity-epic';
      case 'legendary': return 'rarity-legendary';
      case 'champion': return 'rarity-champion';
      default: return 'rarity-common';
    }
  }

  rarityEmoji(rarity?: string): string {
    switch (rarity) {
      case 'common': return '⚪';
      case 'rare': return '🟠';
      case 'epic': return '🟣';
      case 'legendary': return '🌟';
      case 'champion': return '👑';
      default: return '✨';
    }
  }

  typeEmoji(type?: string | null): string {
    switch (type) {
      case 'troop': return '⚔️';
      case 'spell': return '🔮';
      case 'building': return '🏰';
      default: return '🎴';
    }
  }
}
