/* ============================================
   WINRATE BADGE COMPONENT
   Displays winrate with color coding
   ============================================ */

import { NgClass } from '@angular/common';
import { Component, computed, input } from '@angular/core';

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
  imports: [NgClass],
  templateUrl: './winrate-badge.component.html',
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

  /** Tailwind classes for the badge */
  readonly badgeClasses = computed(() => {
    const sizeMap: Record<string, string> = {
      sm: 'text-[0.7rem] px-2 py-0.5',
      md: 'text-[0.8rem] px-3 py-1',
      lg: 'text-[0.95rem] px-3.5 py-1.5',
    };
    const wr = this.winrate();
    const color =
      wr >= 55 ? 'bg-green-500/10 border border-green-500/35 text-green-400'
        : wr >= 47 ? 'bg-[#f6c237]/10 border border-[#f6c237]/30 text-[#f6c237]'
          : 'bg-red-500/10 border border-red-500/30 text-red-400';
    return `${sizeMap[this.size()] ?? sizeMap['md']} ${color}`;
  });
}
