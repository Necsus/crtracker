import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { PlayerService } from '../10_bll/player.service';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

export type TabId = 'profil' | 'battlelog' | 'deck-stats';

export interface MockDeckStat {
  id: number;
  cards: { name: string; icon: string }[];
  wins: number;
  losses: number;
  winrate: number;
}

const ICON = (slug: string) =>
  `https://api-assets.clashroyale.com/cards/300/${slug}.png`;

const MOCK_DECK_STATS: Record<string, MockDeckStat[]> = {
  current: [
    {
      id: 1,
      cards: [
        { name: 'Hog Rider', icon: ICON('Ubu0oUl8tZkusnkZf8Xv9Vno5IO29Y-jbZ4fhoNJ5oc') },
        { name: 'Musketeer', icon: ICON('Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds') },
        { name: 'Ice Spirit', icon: ICON('lv1budiafU9XmSdrDkk0NYyqASAFYyZ06CPysXKZXlA') },
        { name: 'The Log', icon: ICON('_iDwuDLexHPFZ_x4_a0eP-rxCS6vwWgTs6DLauwwoaY') },
        { name: 'Cannon', icon: ICON('nZK1y-beLxO5vnlyUhK6-2zH2NzXJwqykcosqQ1cmZ8') },
        { name: 'Ice Golem', icon: ICON('r05cmpwV1o7i7FHodtZwW3fmjbXCW34IJCsDEV5cZC4') },
        { name: 'Skeletons', icon: ICON('oO7iKMU5m0cdxhYPZA3nWQiAUh2yoGgdThLWB1rVSec') },
        { name: 'Fireball', icon: ICON('lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc') },
      ],
      wins: 38, losses: 19, winrate: 67,
    },
    {
      id: 2,
      cards: [
        { name: 'Giant', icon: ICON('jy-AF9KkNRhKZNPy0GJrexFMCalBRwSWxnYTjNj2i0c') },
        { name: 'Witch', icon: ICON('b4FkDGLMwCKM6Xw6wOIZQP-BjS_N8MO-DfUjAFCED8') },
        { name: 'Musketeer', icon: ICON('Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds') },
        { name: 'Ice Spirit', icon: ICON('lv1budiafU9XmSdrDkk0NYyqASAFYyZ06CPysXKZXlA') },
        { name: 'The Log', icon: ICON('_iDwuDLexHPFZ_x4_a0eP-rxCS6vwWgTs6DLauwwoaY') },
        { name: 'Fireball', icon: ICON('lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc') },
        { name: 'Skeletons', icon: ICON('oO7iKMU5m0cdxhYPZA3nWQiAUh2yoGgdThLWB1rVSec') },
        { name: 'Cannon', icon: ICON('nZK1y-beLxO5vnlyUhK6-2zH2NzXJwqykcosqQ1cmZ8') },
      ],
      wins: 12, losses: 14, winrate: 46,
    },
  ],
  previous: [
    {
      id: 1,
      cards: [
        { name: 'Hog Rider', icon: ICON('Ubu0oUl8tZkusnkZf8Xv9Vno5IO29Y-jbZ4fhoNJ5oc') },
        { name: 'Musketeer', icon: ICON('Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds') },
        { name: 'Ice Spirit', icon: ICON('lv1budiafU9XmSdrDkk0NYyqASAFYyZ06CPysXKZXlA') },
        { name: 'The Log', icon: ICON('_iDwuDLexHPFZ_x4_a0eP-rxCS6vwWgTs6DLauwwoaY') },
        { name: 'Cannon', icon: ICON('nZK1y-beLxO5vnlyUhK6-2zH2NzXJwqykcosqQ1cmZ8') },
        { name: 'Ice Golem', icon: ICON('r05cmpwV1o7i7FHodtZwW3fmjbXCW34IJCsDEV5cZC4') },
        { name: 'Skeletons', icon: ICON('oO7iKMU5m0cdxhYPZA3nWQiAUh2yoGgdThLWB1rVSec') },
        { name: 'Fireball', icon: ICON('lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc') },
      ],
      wins: 55, losses: 27, winrate: 67,
    },
    {
      id: 2,
      cards: [
        { name: 'Giant', icon: ICON('jy-AF9KkNRhKZNPy0GJrexFMCalBRwSWxnYTjNj2i0c') },
        { name: 'Witch', icon: ICON('b4FkDGLMwCKM6Xw6wOIZQP-BjS_N8MO-DfUjAFCED8') },
        { name: 'Musketeer', icon: ICON('Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds') },
        { name: 'Ice Spirit', icon: ICON('lv1budiafU9XmSdrDkk0NYyqASAFYyZ06CPysXKZXlA') },
        { name: 'The Log', icon: ICON('_iDwuDLexHPFZ_x4_a0eP-rxCS6vwWgTs6DLauwwoaY') },
        { name: 'Fireball', icon: ICON('lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc') },
        { name: 'Skeletons', icon: ICON('oO7iKMU5m0cdxhYPZA3nWQiAUh2yoGgdThLWB1rVSec') },
        { name: 'Cannon', icon: ICON('nZK1y-beLxO5vnlyUhK6-2zH2NzXJwqykcosqQ1cmZ8') },
      ],
      wins: 30, losses: 35, winrate: 46,
    },
    {
      id: 3,
      cards: [
        { name: 'Hog Rider', icon: ICON('Ubu0oUl8tZkusnkZf8Xv9Vno5IO29Y-jbZ4fhoNJ5oc') },
        { name: 'Ice Spirit', icon: ICON('lv1budiafU9XmSdrDkk0NYyqASAFYyZ06CPysXKZXlA') },
        { name: 'Skeletons', icon: ICON('oO7iKMU5m0cdxhYPZA3nWQiAUh2yoGgdThLWB1rVSec') },
        { name: 'The Log', icon: ICON('_iDwuDLexHPFZ_x4_a0eP-rxCS6vwWgTs6DLauwwoaY') },
        { name: 'Cannon', icon: ICON('nZK1y-beLxO5vnlyUhK6-2zH2NzXJwqykcosqQ1cmZ8') },
        { name: 'Ice Golem', icon: ICON('r05cmpwV1o7i7FHodtZwW3fmjbXCW34IJCsDEV5cZC4') },
        { name: 'Fireball', icon: ICON('lZD9MILQv7O-P3XBr_xOLS5idwuz3_7Ws9G60U36yhc') },
        { name: 'Musketeer', icon: ICON('Tex1C48UTq9FKtAX-3tzG0FJmc9jzncUZG3bb5Vf-Ds') },
      ],
      wins: 8, losses: 5, winrate: 62,
    },
  ],
  all: [],
};

// Merge all seasons for "all time"
MOCK_DECK_STATS['all'] = Object.values(MOCK_DECK_STATS).flat();

@Component({
  selector: 'app-player-detail',
  standalone: true,
  imports: [RouterLink, LoadingSpinnerComponent, DatePipe],
  templateUrl: './player-detail.component.html',
})
export class PlayerDetailComponent implements OnInit {
  service = inject(PlayerService);
  private route = inject(ActivatedRoute);

  activeTab = signal<TabId>('profil');
  selectedSeason = signal<'current' | 'previous' | 'all'>('current');

  readonly tabs: { id: TabId; label: string; icon: string }[] = [
    { id: 'profil', label: 'Profil', icon: '👤' },
    { id: 'battlelog', label: 'Battle Log', icon: '⚔️' },
    { id: 'deck-stats', label: 'Stats Decks', icon: '📊' },
  ];

  readonly seasons = [
    { id: 'current' as const, label: 'Saison actuelle' },
    { id: 'previous' as const, label: 'Saison précédente' },
    { id: 'all' as const, label: 'Tout le temps' },
  ];

  readonly mockDeckStats = MOCK_DECK_STATS;

  get currentDeckStats(): MockDeckStat[] {
    return this.mockDeckStats[this.selectedSeason()];
  }

  ngOnInit(): void {
    const tag = this.route.snapshot.paramMap.get('tag') ?? '';
    this.service.loadPlayer(tag);
    this.service.loadBattles(tag);
  }

  winrateColor(wr: number | null): string {
    if (wr === null) return '#6b7280';
    if (wr >= 55) return '#22c55e';
    if (wr >= 47) return '#eab308';
    return '#ef4444';
  }

  polLeagueLabel(league: number | null): string {
    if (league === null) return '—';
    const labels: Record<number, string> = {
      1: 'Bronze I', 2: 'Bronze II', 3: 'Bronze III',
      4: 'Silver I', 5: 'Silver II', 6: 'Gold',
      7: 'Master', 8: 'Champion', 9: 'Grand Champion', 10: 'Ultimate Champion',
    };
    return labels[league] ?? `League ${league}`;
  }

  roleLabel(role: string | null): string {
    const map: Record<string, string> = {
      member: 'Membre', elder: 'Ancien',
      coLeader: 'Co-Chef', leader: 'Chef',
    };
    return role ? (map[role] ?? role) : '';
  }

  formatNumber(n: number | null | undefined): string {
    if (n == null) return '—';
    return n.toLocaleString('fr-FR');
  }

  cardDisplayLevel(card: { level?: number; maxLevel?: number }): number {
    return (card.level ?? 1) + (16 - (card.maxLevel ?? 16));
  }

  cardSlotType(index: number, card: { iconUrls?: { evolutionMedium?: string; heroMedium?: string } }): 'evolution' | 'hero' | 'normal' {
    if (index === 0) return 'evolution';
    if (index === 1) return 'hero';
    if (index === 2) {
      if (card.iconUrls?.evolutionMedium) return 'evolution';
      if (card.iconUrls?.heroMedium) return 'hero';
    }
    return 'normal';
  }

  cardImage(index: number, card: { iconUrls?: { medium?: string; evolutionMedium?: string; heroMedium?: string } }): string {
    const type = this.cardSlotType(index, card);
    if (type === 'evolution' && card.iconUrls?.evolutionMedium) return card.iconUrls.evolutionMedium;
    if (type === 'hero' && card.iconUrls?.heroMedium) return card.iconUrls.heroMedium;
    return card.iconUrls?.medium ?? '';
  }
}

