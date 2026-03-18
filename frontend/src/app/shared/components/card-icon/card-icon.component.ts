/* ============================================
   CARD ICON COMPONENT
   Displays a single Clash Royale card with elixir cost
   ============================================ */

import { NgClass } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import type { Card } from '../../../01_models/deck.model';

/**
 * Card Icon Component - Dumb/presentational component
 *
 * Displays a card with:
 * - Card icon/image (with fallback placeholder)
 * - Elixir cost indicator
 * - Rarity border glow
 */
@Component({
  selector: 'app-card-icon',
  standalone: true,
  imports: [NgClass],
  templateUrl: './card-icon.component.html',
})
export class CardIconComponent {
  /** Card data input (required signal input) */
  readonly card = input.required<Card>();

  /** Size variant for the card */
  readonly size = input<'sm' | 'md' | 'lg'>('md');

  /** Whether to show elixir cost */
  readonly showElixir = input(true);

  /* ============================================
     COMPUTED PROPERTIES
     ============================================ */

  /** CSS classes based on card properties */
  readonly cssClasses = computed(() => {
    const card = this.card();
    const size = this.size();

    return {
      'card-icon': true,
      [`card-icon--${size}`]: true,
      [`card-icon--${card.rarity}`]: true,
      'card-icon--spell': card.type === 'spell',
      'card-icon--troop': card.type === 'troop',
      'card-icon--building': card.type === 'building',
      'card-icon--evolved': !!card.evolved,
      'card-icon--golden': !!card.golden,
    };
  });

  /** Whether the card is evolved */
  readonly isEvolved = computed(() => !!this.card().evolved);

  /** Whether the card has a golden skin */
  readonly isGolden = computed(() => !!this.card().golden);

  /** Elixir color based on cost */
  readonly elixirColor = computed(() => {
    const elixir = this.card().elixir;
    if (elixir <= 3) return 'low';
    if (elixir <= 5) return 'medium';
    return 'high';
  });

  /** Fallback initial for no-icon case */
  readonly initial = computed(() => {
    return this.card().name.charAt(0).toUpperCase();
  });

  /** Card image URL or placeholder */
  readonly imageUrl = computed(() => {
    return this.card().icon_url || '';
  });
}
