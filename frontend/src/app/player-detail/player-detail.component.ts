import { DatePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { PlayerService } from '../10_bll/player.service';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-player-detail',
  standalone: true,
  imports: [RouterLink, LoadingSpinnerComponent, DatePipe],
  templateUrl: './player-detail.component.html',
})
export class PlayerDetailComponent implements OnInit {
  service = inject(PlayerService);
  private route = inject(ActivatedRoute);

  ngOnInit(): void {
    const tag = this.route.snapshot.paramMap.get('tag') ?? '';
    this.service.loadPlayer(tag);
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

  /** Détermine le type de slot selon la position dans le deck. */
  cardSlotType(index: number, card: { iconUrls?: { evolutionMedium?: string; heroMedium?: string } }): 'evolution' | 'hero' | 'normal' {
    if (index === 0) return 'evolution';
    if (index === 1) return 'hero';
    if (index === 2) {
      if (card.iconUrls?.evolutionMedium) return 'evolution';
      if (card.iconUrls?.heroMedium) return 'hero';
    }
    return 'normal';
  }

  /** Retourne l'URL d'image adaptée au type de slot. */
  cardImage(index: number, card: { iconUrls?: { medium?: string; evolutionMedium?: string; heroMedium?: string } }): string {
    const type = this.cardSlotType(index, card);
    if (type === 'evolution' && card.iconUrls?.evolutionMedium) return card.iconUrls.evolutionMedium;
    if (type === 'hero' && card.iconUrls?.heroMedium) return card.iconUrls.heroMedium;
    return card.iconUrls?.medium ?? '';
  }
}
