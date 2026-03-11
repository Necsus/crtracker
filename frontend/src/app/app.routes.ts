/* ============================================
   ROOT APP ROUTES
   Lazy-loaded feature routes
   ============================================ */

import { Routes } from '@angular/router';

export const appRoutes: Routes = [
  {
    path: '',
    loadChildren: () =>
      import('./deck-search/deck-search.routes').then((m) => m.DECK_SEARCH_ROUTES),
  },
  {
    path: 'battles',
    loadChildren: () =>
      import('./battles-log/battles-log.routes').then((m) => m.BATTLES_LOG_ROUTES),
  },
  {
    path: 'decks/:id',
    loadChildren: () =>
      import('./deck-detail/deck-detail.routes').then((m) => m.DECK_DETAIL_ROUTES),
  },
  {
    path: 'cards/:id',
    loadChildren: () =>
      import('./card-detail/card-detail.routes').then((m) => m.CARD_DETAIL_ROUTES),
  },
  {
    path: 'cards',
    loadChildren: () =>
      import('./cards-browser/cards-browser.routes').then((m) => m.CARDS_BROWSER_ROUTES),
  },
  {
    path: 'oracle',
    loadChildren: () =>
      import('./oracle-detail/oracle-detail.routes').then((m) => m.ORACLE_DETAIL_ROUTES),
  },
  {
    path: 'players',
    loadChildren: () =>
      import('./players-list/players-list.routes').then((m) => m.PLAYERS_LIST_ROUTES),
  },
  {
    path: 'players/:tag',
    loadChildren: () =>
      import('./player-detail/player-detail.routes').then((m) => m.PLAYER_DETAIL_ROUTES),
  },
  {
    path: '**',
    redirectTo: '',
    pathMatch: 'full',
  },
];
