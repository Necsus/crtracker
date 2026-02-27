/* ============================================
   ORACLE BUSINESS LOGIC LAYER
   State management for Oracle analysis using Signals
   ============================================ */

import { inject, Injectable, signal, computed } from '@angular/core';
import { tap, catchError, of } from 'rxjs';

import type { OracleMatchup, OracleAdvice } from '../01_models/deck.model';
import type { LoadingState } from '../01_models/app.model';
import { OracleDal } from '../00_dal/oracle.dal';

/**
 * Oracle Service - Manages Oracle analysis state
 *
 * Responsibilities:
 * - Fetch and cache matchup analysis
 * - Manage loading/error states
 * - Provide reactive state via computed signals
 * - Group advice by category for UI display
 */
@Injectable({ providedIn: 'root' })
export class OracleService {
  private readonly oracleDal = inject(OracleDal);

  /* ============================================
     STATE SIGNALS
     ============================================ */

  /** Loading state for Oracle analysis */
  private readonly loadingState = signal<LoadingState>('idle');

  /** Current error message */
  private readonly error = signal<string | null>(null);

  /** Current matchup analysis */
  private readonly currentMatchup = signal<OracleMatchup | null>(null);

  /** Cache for matchup analyses by key */
  private readonly matchupCache = new Map<string, OracleMatchup>();

  /* ============================================
     COMPUTED SIGNALS (READ-ONLY)
     ============================================ */

  /** Whether analysis is loading */
  readonly isLoading = computed(() => this.loadingState() === 'loading');

  /** Whether there's an error */
  readonly hasError = computed(() => this.error() !== null);

  /** The error message */
  readonly errorMessage = computed(() => this.error());

  /** Current matchup as readonly */
  readonly matchup = computed(() => this.currentMatchup());

  /** Advice grouped by category */
  readonly groupedAdvice = computed(() => {
    const matchup = this.currentMatchup();
    if (!matchup) {
      return [];
    }

    // Group advice by category
    const groups = new Map<string, OracleAdvice[]>();

    for (const advice of matchup.advice) {
      const category = advice.category.name;
      if (!groups.has(category)) {
        groups.set(category, []);
      }
      groups.get(category)!.push(advice);
    }

    // Convert to array and sort by priority
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

    return Array.from(groups.entries()).map(([category, items]) => ({
      category,
      items: items.sort((a, b) => priorityOrder[a.category.priority] - priorityOrder[b.category.priority]),
      highestPriority: items.reduce((highest, item) =>
        priorityOrder[item.category.priority] < priorityOrder[highest] ? item.category.priority : highest,
        items[0]?.category.priority || 'medium'
      ),
    })).sort((a, b) => priorityOrder[a.highestPriority] - priorityOrder[b.highestPriority]);
  });

  /** Winrate prediction formatted */
  readonly winrateDisplay = computed(() => {
    const matchup = this.currentMatchup();
    if (!matchup) {
      return '';
    }
    return `${matchup.winrate_prediction.toFixed(1)}%`;
  });

  /** Difficulty label */
  readonly difficultyLabel = computed(() => {
    const matchup = this.currentMatchup();
    if (!matchup) {
      return '';
    }
    const labels = {
      favorable: 'Favorable',
      even: 'Even Matchup',
      unfavorable: 'Unfavorable',
      hard: 'Difficult',
    };
    return labels[matchup.difficulty];
  });

  /** Total advice count */
  readonly adviceCount = computed(() => {
    return this.currentMatchup()?.advice.length || 0;
  });

  /* ============================================
     OPERATIONS
     ============================================ */

  /**
   * Load Oracle analysis for a matchup
   */
  loadMatchupAnalysis(
    playerDeckId: number,
    opponentDeckId: number,
    forceRefresh = false,
  ): void {
    // Check cache first
    const cacheKey = `${playerDeckId}_vs_${opponentDeckId}`;

    if (!forceRefresh) {
      const cached = this.matchupCache.get(cacheKey);
      if (cached) {
        this.currentMatchup.set(cached);
        this.loadingState.set('success');
        this.error.set(null);
        return;
      }
    }

    // Fetch from API
    this.loadingState.set('loading');
    this.error.set(null);

    this.oracleDal.getMatchupAnalysis(playerDeckId, opponentDeckId, forceRefresh).pipe(
      tap(matchup => {
        this.currentMatchup.set(matchup);

        // Update cache
        this.matchupCache.set(cacheKey, matchup);

        this.loadingState.set('success');
      }),
      catchError(err => {
        this.loadingState.set('error');
        this.error.set(err.userMessage || 'Failed to load Oracle analysis');
        return of(null);
      })
    ).subscribe();
  }

  /* ============================================
     UTILITIES
     ============================================ */

  /**
   * Clear the current matchup
   */
  clearMatchup(): void {
    this.currentMatchup.set(null);
    this.loadingState.set('idle');
    this.error.set(null);
  }

  /**
   * Clear the current error
   */
  clearError(): void {
    this.error.set(null);
  }

  /**
   * Check if a specific matchup is cached
   */
  isCached(playerDeckId: number, opponentDeckId: number): boolean {
    const cacheKey = `${playerDeckId}_vs_${opponentDeckId}`;
    return this.matchupCache.has(cacheKey);
  }
}
