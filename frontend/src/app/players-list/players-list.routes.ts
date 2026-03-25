import { Routes } from '@angular/router';
import { PlayersListComponent } from './players-list.component';

export const PLAYERS_LIST_ROUTES: Routes = [
  { path: '', component: PlayersListComponent },
  {
    path: ':tag',
    loadChildren: () =>
      import('../player-detail/player-detail.routes').then((m) => m.PLAYER_DETAIL_ROUTES),
  },
];
