import { Routes } from '@angular/router';

export const ARCHETYPES_BROWSER_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./archetypes-browser.component').then(m => m.ArchetypesBrowserComponent),
    pathMatch: 'full',
  },
];
