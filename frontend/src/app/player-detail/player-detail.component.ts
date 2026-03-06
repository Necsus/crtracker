/* ============================================
   PLAYER DETAIL COMPONENT
   Full profile page for a single Clash Royale player
   ============================================ */

import { DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { DeckDal } from '../00_dal/deck.dal';
import type { PlayerProfile } from '../01_models/deck.model';
import { LoadingSpinnerComponent } from '../shared/components/loading-spinner/loading-spinner.component';

@Component({
  selector: 'app-player-detail',
  standalone: true,
  imports: [RouterLink, LoadingSpinnerComponent, DecimalPipe],
  templateUrl: './player-detail.component.html',
})
export class PlayerDetailComponent implements OnInit {
  private readonly dal = inject(DeckDal);
  private readonly route = inject(ActivatedRoute);

  /* ── State ──────────────────────────────────── */
  readonly player = signal<PlayerProfile | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    const tag = this.route.snapshot.paramMap.get('tag') ?? '';
    this.dal.getPlayer(tag).subscribe({
      next: (p) => {
        this.player.set(p);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Player not found or failed to load.');
        this.loading.set(false);
      },
    });
  }

  /* ── Helpers ─────────────────────────────────── */

  winRate(p: PlayerProfile): number {
    const total = (p.wins ?? 0) + (p.losses ?? 0);
    if (total === 0) return 0;
    return ((p.wins ?? 0) / total) * 100;
  }

  avgElixir(p: PlayerProfile): number {
    const cards = p.current_deck ?? [];
    const withCost = cards.filter((c) => c.elixir_cost !== null);
    if (withCost.length === 0) return 0;
    return withCost.reduce((sum, c) => sum + (c.elixir_cost ?? 0), 0) / withCost.length;
  }
}
