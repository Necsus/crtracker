import { Routes } from '@angular/router';

export const PLAYER_DETAIL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./player-detail.component').then((m) => m.PlayerDetailComponent),
  },
];
