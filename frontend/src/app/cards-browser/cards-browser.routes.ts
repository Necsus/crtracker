import { Routes } from '@angular/router';

export const CARDS_BROWSER_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./cards-browser.component').then((m) => m.CardsBrowserComponent),
  },
];
