/* ============================================
   MATCHUP CARD COMPONENT
   Displays a single matchup with winrate
   ============================================ */

import { NgClass } from '@angular/common';
import { Component, computed, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import type { MatchupStats } from '../../../01_models/deck.model';

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
  imports: [RouterLink, NgClass],
  templateUrl: './matchup-card.component.html',
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

  /** Tailwind classes for the winrate badge in this card */
  readonly wrBadgeClasses = computed(() => {
    const winrate = this.matchup().winrate;
    if (winrate >= 55) return 'bg-green-500/10 border border-green-500/30 text-green-400';
    if (winrate >= 47) return 'bg-[#f6c237]/10 border border-[#f6c237]/25 text-[#f6c237]';
    return 'bg-red-500/10 border border-red-500/25 text-red-400';
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
