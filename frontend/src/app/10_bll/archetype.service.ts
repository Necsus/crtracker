/* ============================================
   ARCHETYPE SERVICE (BLL)
   State management for archetypes using Signals
   ============================================ */

import { computed, inject, Injectable, signal } from '@angular/core';
import { catchError, of, tap } from 'rxjs';

import { ArchetypeDal } from '../00_dal/archetype.dal';
import { DeckDal } from '../00_dal/deck.dal';
import type { LoadingState } from '../01_models/app.model';
import type {
  ArchetypeListItem,
  ArchetypeWithVariants,
  Card,
  CardApiItem,
  DeckMetaStatus,
  MetaStatusValue,
} from '../01_models/deck.model';

/** Display labels for each play style */
export const PLAY_STYLE_LABELS: Record<string, string> = {
  CYCLE: 'Cycle',
  BEATDOWN: 'Beatdown',
  CONTROL: 'Control',
  BRIDGE_SPAM: 'Bridge Spam',
  SIEGE: 'Siège',
  HYBRID: 'Hybride',
};

/** Display labels for each meta status */
export const META_STATUS_LABELS: Record<MetaStatusValue, string> = {
  DOMINANT: 'Dominant',
  VIABLE: 'Viable',
  ANTI_META: 'Anti-Meta',
  OFF_META: 'Off-Meta',
  UNCLASSIFIED: 'Non classifié',
};

/** Tailwind colour classes for each meta status */
export const META_STATUS_COLORS: Record<MetaStatusValue, string> = {
  DOMINANT: 'bg-red-500/20 border-red-500/40 text-red-400',
  VIABLE: 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400',
  ANTI_META: 'bg-purple-500/20 border-purple-500/40 text-purple-400',
  OFF_META: 'bg-slate-500/20 border-slate-500/40 text-slate-400',
  UNCLASSIFIED: 'bg-slate-700/20 border-slate-700/40 text-slate-500',
};

@Injectable({ providedIn: 'root' })
export class ArchetypeService {
  private readonly dal = inject(ArchetypeDal);
  private readonly deckDal = inject(DeckDal);

  /* ============================================
     STATE SIGNALS
     ============================================ */

  private readonly loadingState = signal<LoadingState>('idle');
  private readonly error = signal<string | null>(null);

  /** Flat list of all archetypes */
  private readonly allArchetypes = signal<ArchetypeListItem[]>([]);

  /** Archetype tree (roots with variants) */
  private readonly archetypeTree = signal<ArchetypeWithVariants[]>([]);

  /** Meta history for the currently viewed deck */
  private readonly deckMetaHistory = signal<DeckMetaStatus[]>([]);

  /**
   * Card catalog: keyed by both numeric id string AND kebab slug of the name.
   * Used by the archetypes browser to resolve core_cards → images.
   */
  private readonly _cardCatalog = signal<Map<string, CardApiItem>>(new Map());

  /* ============================================
     COMPUTED READ-ONLY SIGNALS
     ============================================ */

  readonly isLoading = computed(() => this.loadingState() === 'loading');
  readonly hasError = computed(() => this.error() !== null);
  readonly errorMessage = computed(() => this.error());

  /** All archetypes as a flat list */
  readonly archetypes = computed(() => this.allArchetypes());

  /** Archetype tree (root nodes with children) */
  readonly tree = computed(() => this.archetypeTree());

  /** Only timeless ("Indemodable") archetypes */
  readonly timelessArchetypes = computed(() =>
    this.allArchetypes().filter(a => a.is_timeless)
  );

  /** Meta history for current deck */
  readonly metaHistory = computed(() => this.deckMetaHistory());

  /** Quick lookup map: id → archetype */
  readonly archetypeById = computed(() => {
    const map = new Map<number, ArchetypeListItem>();
    this.allArchetypes().forEach(a => map.set(a.id, a));
    return map;
  });

  /* ============================================
     OPERATIONS
     ============================================ */

  /** Load all archetypes (flat) */
  loadArchetypes(): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.dal.listArchetypes().pipe(
      tap(list => {
        this.allArchetypes.set(list);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load archetypes');
        return of([]);
      })
    ).subscribe();
  }

  /** Load the archetype tree (root nodes with variants) */
  loadArchetypeTree(): void {
    this.loadingState.set('loading');
    this.error.set(null);

    this.dal.getArchetypeTree().pipe(
      tap(tree => {
        this.archetypeTree.set(tree);
        // Also populate the flat list from the tree for the lookup map
        const flat: ArchetypeListItem[] = [];
        tree.forEach(root => {
          flat.push(root);
          root.variants.forEach(v => flat.push(v));
        });
        this.allArchetypes.set(flat);
        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load archetype tree');
        return of([]);
      })
    ).subscribe();
  }

  /** Load meta status history for a given deck */
  loadMetaHistory(deckId: number): void {
    this.dal.getMetaHistory(deckId).pipe(
      tap(history => this.deckMetaHistory.set(history)),
      catchError(() => of([]))
    ).subscribe();
  }

  /** Resolve an archetype by ID from the in-memory cache */
  getArchetypeName(archetypeId: number | null | undefined): string | null {
    if (archetypeId == null) return null;
    return this.archetypeById().get(archetypeId)?.name ?? null;
  }

  /** Clear error state */
  clearError(): void {
    this.error.set(null);
  }

  /**
   * Load the full card catalogue once and build a lookup map.
   * Keyed by:
   *   - card.id (numeric string, e.g. "26000036")
   *   - kebab slug of the card name (e.g. "hog-rider") for seed-data fallback
   * Safe to call multiple times — skips if already loaded.
   */
  loadCards(): void {
    if (this._cardCatalog().size > 0) return;

    this.deckDal.listCards({ limit: 500 }).pipe(
      tap(cards => {
        const map = new Map<string, CardApiItem>();
        for (const card of cards) {
          map.set(String(card.id), card);
          map.set(this._slugify(card.name), card);
        }
        this._cardCatalog.set(map);
      }),
      catchError(() => of([]))
    ).subscribe();
  }

  /**
   * Resolve a core_cards entry (numeric id or slug) to a displayable Card.
   * Falls back to a minimal stub so CardIconComponent can always render.
   */
  resolveCard(id: string): Card {
    const found = this._cardCatalog().get(String(id));
    if (found) return found as Card;
    // Graceful fallback: turn slug into a readable name
    return {
      id,
      name: this._slugToName(id),
      elixir: 0,
      rarity: 'common',
    };
  }

  private _slugify(name: string): string {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  }

  private _slugToName(slug: string): string {
    return slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }
}
