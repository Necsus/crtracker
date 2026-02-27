/* ============================================
   ORACLE DETAIL FEATURE ROUTES
   ============================================ */

import { Routes } from '@angular/router';
import { OracleDetailComponent } from './oracle-detail.component';

export const ORACLE_DETAIL_ROUTES: Routes = [
  {
    path: ':playerDeckId/:opponentDeckId',
    component: OracleDetailComponent,
  },
];
