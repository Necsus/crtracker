import { Routes } from '@angular/router';

export const appRoutes: Routes = [
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
    path: '',
    redirectTo: 'players',
    pathMatch: 'full',
  },
  {
    path: '**',
    redirectTo: 'players',
    pathMatch: 'full',
  },
];
