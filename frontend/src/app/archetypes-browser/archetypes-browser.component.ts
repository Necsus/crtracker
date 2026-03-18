/* ============================================
   ARCHETYPES BROWSER FEATURE COMPONENT
   Displays the full archetype catalogue with tree view
   ============================================ */

import { NgClass } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';

import { ArchetypeDal } from '../00_dal/archetype.dal';
import type { ArchetypeListItem, ArchetypePlayStyle, ArchetypeWithVariants, Card } from '../01_models/deck.model';
import { ArchetypeService, META_STATUS_COLORS, META_STATUS_LABELS, PLAY_STYLE_LABELS } from '../10_bll/archetype.service';
import { CardIconComponent } from '../shared/components/card-icon/card-icon.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

const PLAY_STYLE_ICONS: Record<ArchetypePlayStyle, string> = {
  CYCLE: '🔄',
  BEATDOWN: '💪',
  CONTROL: '🛡️',
  BRIDGE_SPAM: '⚡',
  SIEGE: '🏹',
  HYBRID: '⚗️',
};

const PLAY_STYLE_COLORS: Record<ArchetypePlayStyle, string> = {
  CYCLE: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-400',
  BEATDOWN: 'bg-red-500/15 border-red-500/30 text-red-400',
  CONTROL: 'bg-blue-500/15 border-blue-500/30 text-blue-400',
  BRIDGE_SPAM: 'bg-yellow-500/15 border-yellow-500/30 text-yellow-400',
  SIEGE: 'bg-orange-500/15 border-orange-500/30 text-orange-400',
  HYBRID: 'bg-purple-500/15 border-purple-500/30 text-purple-400',
};

@Component({
  selector: 'app-archetypes-browser',
  standalone: true,
  imports: [NgClass, LoadingSpinnerComponent, CardIconComponent],
  templateUrl: './archetypes-browser.component.html',
})
export class ArchetypesBrowserComponent implements OnInit {
  private readonly dal = inject(ArchetypeDal);
  private readonly archetypeService = inject(ArchetypeService);

  readonly tree = signal<ArchetypeWithVariants[]>([]);
  readonly isLoading = signal(true);
  readonly error = signal<string | null>(null);

  /** Active play-style filter (null = show all) */
  readonly activeFilter = signal<ArchetypePlayStyle | null>(null);

  /** Whether to show only timeless archetypes */
  readonly timelessOnly = signal(false);

  /** Which root node is expanded */
  readonly expandedId = signal<number | null>(null);

  readonly playStyleIcons = PLAY_STYLE_ICONS;
  readonly playStyleColors = PLAY_STYLE_COLORS;
  readonly playStyleLabels = PLAY_STYLE_LABELS;
  readonly metaStatusColors = META_STATUS_COLORS;
  readonly metaStatusLabels = META_STATUS_LABELS;

  readonly allPlayStyles: ArchetypePlayStyle[] = [
    'CYCLE', 'BEATDOWN', 'CONTROL', 'BRIDGE_SPAM', 'SIEGE', 'HYBRID',
  ];

  readonly filteredTree = computed(() => {
    let roots = this.tree();
    if (this.timelessOnly()) {
      roots = roots.filter(r => r.is_timeless || r.variants.some(v => v.is_timeless));
    }
    const filter = this.activeFilter();
    if (filter) {
      roots = roots.filter(r => r.play_style === filter || r.variants.some(v => v.play_style === filter));
    }
    return roots;
  });

  readonly totalCount = computed(() => {
    const t = this.tree();
    return t.reduce((acc, r) => acc + 1 + r.variants.length, 0);
  });

  readonly timelessCount = computed(() =>
    this.tree().reduce(
      (acc, r) => acc + (r.is_timeless ? 1 : 0) + r.variants.filter(v => v.is_timeless).length,
      0,
    )
  );

  ngOnInit(): void {
    this.archetypeService.loadCards();
    this.dal.getArchetypeTree().subscribe({
      next: tree => {
        this.tree.set(tree);
        this.isLoading.set(false);
      },
      error: () => {
        this.error.set('Failed to load archetypes.');
        this.isLoading.set(false);
      },
    });
  }

  toggleExpand(id: number): void {
    this.expandedId.set(this.expandedId() === id ? null : id);
  }

  setFilter(style: ArchetypePlayStyle | null): void {
    this.activeFilter.set(style);
  }

  toggleTimeless(): void {
    this.timelessOnly.set(!this.timelessOnly());
  }

  variantBadge(variant: ArchetypeListItem): string {
    return variant.is_timeless ? '★ ' : '';
  }
  /** Resolve a core_card id/slug to a displayable Card for CardIconComponent */
  resolveCard(id: string): Card {
    return this.archetypeService.resolveCard(id);
  }
}
