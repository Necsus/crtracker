import { NgTemplateOutlet } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

import { PlayerListItem } from '../01_models/player.model';
import { PlayerService } from '../10_bll/player.service';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-players-list',
  standalone: true,
  imports: [LoadingSpinnerComponent, NgTemplateOutlet],
  templateUrl: './players-list.component.html',
})
export class PlayersListComponent implements OnInit, OnDestroy {
  service = inject(PlayerService);
  private router = inject(Router);

  searchQuery = signal('');
  private searchSubject = new Subject<string>();

  ngOnInit(): void {
    this.service.loadTopPlayers();

    this.searchSubject.pipe(
      debounceTime(400),
      distinctUntilChanged(),
    ).subscribe(query => {
      if (query.length === 0) {
        this.service.clearSearch();
      } else if (query.length >= 2) {
        this.service.search(query);
      }
    });
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchQuery.set(value);
    this.searchSubject.next(value);
  }

  navigateToPlayer(tag: string): void {
    this.router.navigate(['/players', tag]);
  }

  polLeagueLabel(league: number | null): string {
    if (league === null) return '';
    const labels: Record<number, string> = {
      1: 'Bronze I', 2: 'Bronze II', 3: 'Bronze III',
      4: 'Silver I', 5: 'Silver II', 6: 'Gold',
      7: 'Master', 8: 'Champion', 9: 'Grand Champion', 10: 'Ultimate Champion',
    };
    return labels[league] ?? `League ${league}`;
  }

  polLeagueColor(league: number | null): string {
    if (!league) return '#6b7280';
    if (league <= 3) return '#cd7f32';
    if (league <= 5) return '#9ca3af';
    if (league === 6) return '#eab308';
    if (league === 7) return '#8b5cf6';
    if (league === 8) return '#3b82f6';
    if (league === 9) return '#ec4899';
    return '#f97316';
  }

  formatNumber(n: number): string {
    if (n >= 1000) return (n / 1000).toFixed(1).replace('.0', '') + 'k';
    return n.toString();
  }

  trackByTag(_: number, player: PlayerListItem): string {
    return player.tag;
  }

  ngOnDestroy(): void {
    this.searchSubject.complete();
  }
}
