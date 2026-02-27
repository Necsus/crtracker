/* ============================================
   ORACLE DATA ACCESS LAYER
   All HTTP requests for Oracle matchup analysis
   ============================================ */

import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import type {
  OracleMatchup,
} from '../01_models/deck.model';
import { buildUrl } from './api.interceptor';

/**
 * Oracle DAL - Handles all Oracle API calls
 *
 * This service makes HTTP requests for matchup analysis
 * and returns Observables without managing state.
 */
@Injectable({ providedIn: 'root' })
export class OracleDal {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/api/v1/oracle';

  /* ============================================
     MATCHUP ANALYSIS
     ============================================ */

  /**
   * Get Oracle analysis for a specific matchup
   * @param playerDeckId Your deck ID
   * @param opponentDeckId Opponent deck ID
   * @param forceRefresh Force regeneration instead of using cache
   */
  getMatchupAnalysis(
    playerDeckId: number,
    opponentDeckId: number,
    forceRefresh = false,
  ): Observable<OracleMatchup> {
    const url = buildUrl(
      `${this.basePath}/matchup/${playerDeckId}/${opponentDeckId}`,
      { force_refresh: forceRefresh }
    );
    return this.http.get<OracleMatchup>(url);
  }
}
