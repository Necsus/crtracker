import { Routes } from '@angular/router';

export const CARD_DETAIL_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./card-detail.component').then((m) => m.CardDetailComponent),
  },
];
