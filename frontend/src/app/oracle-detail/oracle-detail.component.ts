/* ============================================
   ORACLE DETAIL FEATURE COMPONENT
   Comprehensive tactical advice for a matchup
   ============================================ */

import { Component, inject, OnInit, input } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

import type { OracleAdvice } from '../01_models/deck.model';
import { OracleService } from '../10_bll/oracle.service';
import { DeckDisplayComponent } from '../shared/components/deck-display/deck-display.component';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';
import { WinrateBadgeComponent } from '../shared/components/winrate-badge/winrate-badge.component';

/**
 * Oracle Detail Component - Smart component
 *
 * Features:
 * - Display comprehensive tactical advice
 * - Show both decks with cards
 * - Winrate prediction and difficulty
 * - Group advice by category
 * - Exhaustive list of tips (variable count)
 */
@Component({
  selector: 'app-oracle-detail',
  standalone: true,
  imports: [
    DeckDisplayComponent,
    LoadingSpinnerComponent,
    WinrateBadgeComponent,
  ],
  templateUrl: './oracle-detail.component.html',
  styleUrl: './oracle-detail.component.scss',
})
export class OracleDetailComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly oracleService = inject(OracleService);

  /* ============================================
     ROUTE PARAMETERS (Input from route)
     ============================================ */

  readonly playerDeckId = input<number>(0);
  readonly opponentDeckId = input<number>(0);

  /* ============================================
     SIGNALS (READ-ONLY FROM SERVICES)
     ============================================ */

  readonly isLoading = this.oracleService.isLoading;
  readonly hasError = this.oracleService.hasError;
  readonly errorMessage = this.oracleService.errorMessage;
  readonly matchup = this.oracleService.matchup;
  readonly groupedAdvice = this.oracleService.groupedAdvice;
  readonly winrateDisplay = this.oracleService.winrateDisplay;
  readonly difficultyLabel = this.oracleService.difficultyLabel;
  readonly adviceCount = this.oracleService.adviceCount;

  /* ============================================
     LIFECYCLE
     ============================================ */

  ngOnInit(): void {
    // Get deck IDs from route
    const playerId = Number(this.route.snapshot.paramMap.get('playerDeckId'));
    const opponentId = Number(this.route.snapshot.paramMap.get('opponentDeckId'));

    if (playerId && opponentId) {
      this.oracleService.loadMatchupAnalysis(playerId, opponentId);
    } else {
      this.router.navigate(['/']);
    }
  }

  /* ============================================
     ACTIONS
     ============================================ */

  onRefresh(): void {
    const playerId = Number(this.route.snapshot.paramMap.get('playerDeckId'));
    const opponentId = Number(this.route.snapshot.paramMap.get('opponentDeckId'));
    this.oracleService.loadMatchupAnalysis(playerId, opponentId, true);
  }

  onGoBack(): void {
    this.router.navigate(['/']);
  }

  onDismissError(): void {
    this.oracleService.clearError();
  }

  /* ============================================
     HELPERS
     ============================================ */

  getPriorityIcon(priority: string): string {
    const icons = {
      critical: '🔴',
      high: '🟠',
      medium: '🟡',
      low: '🔵',
    };
    return icons[priority as keyof typeof icons] || '⚪';
  }

  getPriorityLabel(priority: string): string {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  }

  getCardName(cardId: string): string {
    return cardId
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleString();
  }
}
