import { Routes } from '@angular/router';

export const PLAYERS_LIST_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./players-list.component').then((m) => m.PlayersListComponent),
  },
];
