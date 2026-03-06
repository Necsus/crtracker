import { Routes } from '@angular/router';

export const BATTLES_LOG_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./battles-log.component').then((m) => m.BattlesLogComponent),
  },
];
