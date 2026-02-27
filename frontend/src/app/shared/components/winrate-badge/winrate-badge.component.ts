/* ============================================
   WINRATE BADGE COMPONENT
   Displays winrate with color coding
   ============================================ */

import { Component, input, computed } from '@angular/core';

/**
 * Winrate Badge Component - Dumb/presentational component
 *
 * Displays:
 * - Winrate percentage
 * - Color-coded background
 * - Optional label
 */
@Component({
  selector: 'app-winrate-badge',
  standalone: true,
  templateUrl: './winrate-badge.component.html',
  styleUrl: './winrate-badge.component.scss',
})
export class WinrateBadgeComponent {
  /** Winrate value (0-100) */
  readonly winrate = input.required<number>();

  /** Size variant */
  readonly size = input<'sm' | 'md' | 'lg'>('md');

  /** Optional label override */
  readonly label = input<string>('');

  /** Whether to show icon */
  readonly showIcon = input(true);

  /* ============================================
     COMPUTED PROPERTIES
     ============================================ */

  /** Color class based on winrate */
  readonly colorClass = computed(() => {
    const wr = this.winrate();
    if (wr >= 55) return 'favorable';
    if (wr >= 47) return 'even';
    return 'unfavorable';
  });

  /** Display label */
  readonly displayLabel = computed(() => {
    return this.label() || `${this.winrate().toFixed(1)}%`;
  });

  /** Icon indicator */
  readonly icon = computed(() => {
    const wr = this.winrate();
    if (wr >= 55) return '▲';
    if (wr >= 47) return '−';
    return '▼';
  });
}
