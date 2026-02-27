/* ============================================
   DECK SEARCH FEATURE ROUTES
   ============================================ */

import { Routes } from '@angular/router';
import { DeckSearchComponent } from './deck-search.component';

export const DECK_SEARCH_ROUTES: Routes = [
  {
    path: '',
    component: DeckSearchComponent,
    pathMatch: 'full',
  },
];
