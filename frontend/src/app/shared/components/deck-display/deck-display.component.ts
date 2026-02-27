/* ============================================
   DECK DISPLAY COMPONENT
   Displays a complete deck with all 8 cards
   ============================================ */

import { Component, input } from '@angular/core';
import type { Deck } from '../../../01_models/deck.model';
import { CardIconComponent } from '../card-icon/card-icon.component';

/**
 * Deck Display Component - Dumb/presentational component
 *
 * Displays:
 * - Deck name and archetype
 * - All 8 cards in a grid
 * - Average elixir cost
 */
@Component({
  selector: 'app-deck-display',
  standalone: true,
  imports: [CardIconComponent],
  templateUrl: './deck-display.component.html',
  styleUrl: './deck-display.component.scss',
})
export class DeckDisplayComponent {
  /** Deck data input */
  readonly deck = input.required<Deck>();

  /** Size variant for cards */
  readonly cardSize = input<'sm' | 'md' | 'lg'>('md');

  /** Whether to show deck metadata */
  readonly showMeta = input(true);

  /** Whether cards are clickable (for navigation) */
  readonly clickable = input(false);
}
