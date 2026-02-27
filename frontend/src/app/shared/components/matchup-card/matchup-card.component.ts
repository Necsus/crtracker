/* ============================================
   MATCHUP CARD COMPONENT
   Displays a single matchup with winrate
   ============================================ */

import { Component, input, output, computed } from '@angular/core';
import type { MatchupStats } from '../../../01_models/deck.model';
import { RouterLink } from '@angular/router';

/**
 * Matchup Card Component - Dumb/presentational component
 *
 * Displays:
 * - Opponent deck name and archetype
 * - Winrate percentage with color coding
 * - Sample size
 * - Clickable to navigate to Oracle detail
 */
@Component({
  selector: 'app-matchup-card',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './matchup-card.component.html',
  styleUrl: './matchup-card.component.scss',
})
export class MatchupCardComponent {
  /** Matchup stats input */
  readonly matchup = input.required<MatchupStats>();

  /** Player deck ID for navigation */
  readonly playerDeckId = input.required<number>();

  /** Whether to show full details */
  readonly showDetails = input(true);

  /** Emitted when clicked (alternative to router link) */
  readonly clicked = output<number>();

  /* ============================================
     COMPUTED PROPERTIES
     ============================================ */

  /** Winrate color class */
  readonly winrateClass = computed(() => {
    const winrate = this.matchup().winrate;
    if (winrate >= 55) return 'favorable';
    if (winrate >= 47) return 'even';
    return 'unfavorable';
  });

  /** Winrate icon */
  readonly winrateIcon = computed(() => {
    const winrate = this.matchup().winrate;
    if (winrate >= 55) return '🟢';
    if (winrate >= 47) return '🟡';
    return '🔴';
  });

  /** Router link to Oracle detail */
  readonly oracleLink = computed(() => {
    return `/oracle/${this.playerDeckId()}/${this.matchup().opponent_deck_id}`;
  });

  /** Format sample size with k suffix */
  formatSampleSize(n: number): string {
    return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : n.toString();
  }
}
