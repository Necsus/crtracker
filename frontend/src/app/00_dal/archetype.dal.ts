/* ============================================
   ARCHETYPE DAL
   HTTP calls for /api/v1/archetypes endpoints
   ============================================ */

import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import type {
  ArchetypeCreate,
  ArchetypeListItem,
  ArchetypeResponse,
  ArchetypeWithVariants,
  DeckMetaStatus,
} from '../01_models/deck.model';
import { buildUrl } from './api.interceptor';

@Injectable({ providedIn: 'root' })
export class ArchetypeDal {
  private readonly http = inject(HttpClient);
  private readonly basePath = '/api/v1/archetypes';

  /** List all archetypes (flat) */
  listArchetypes(): Observable<ArchetypeListItem[]> {
    return this.http.get<ArchetypeListItem[]>(this.basePath);
  }

  /** List only "Indemodable" archetypes */
  listTimeless(): Observable<ArchetypeListItem[]> {
    return this.http.get<ArchetypeListItem[]>(`${this.basePath}/timeless`);
  }

  /** Root archetypes with their variant children */
  getArchetypeTree(): Observable<ArchetypeWithVariants[]> {
    return this.http.get<ArchetypeWithVariants[]>(`${this.basePath}/tree`);
  }

  /** Get a single archetype with its variants */
  getArchetype(id: number): Observable<ArchetypeWithVariants> {
    return this.http.get<ArchetypeWithVariants>(`${this.basePath}/${id}`);
  }

  /** Create a new curated archetype */
  createArchetype(payload: ArchetypeCreate): Observable<ArchetypeResponse> {
    return this.http.post<ArchetypeResponse>(this.basePath, payload);
  }

  /** Update an existing archetype */
  updateArchetype(id: number, payload: ArchetypeCreate): Observable<ArchetypeResponse> {
    return this.http.put<ArchetypeResponse>(`${this.basePath}/${id}`, payload);
  }

  /** Delete an archetype */
  deleteArchetype(id: number): Observable<void> {
    return this.http.delete<void>(`${this.basePath}/${id}`);
  }

  /** Fingerprint all unclassified decks (admin/background job) */
  classifyAll(): Observable<{ matched: number; unmatched: number; errors: number }> {
    return this.http.post<{ matched: number; unmatched: number; errors: number }>(
      `${this.basePath}/classify/all`,
      {}
    );
  }

  /** Fingerprint a single deck */
  classifyDeck(deckId: number): Observable<{
    deck_id: number;
    deck_key: string | null;
    archetype_id: number | null;
    archetype_name: string | null;
  }> {
    return this.http.post<{
      deck_id: number;
      deck_key: string | null;
      archetype_id: number | null;
      archetype_name: string | null;
    }>(`${this.basePath}/classify/${deckId}`, {});
  }

  /** Get competitive meta-status history for a deck */
  getMetaHistory(deckId: number): Observable<DeckMetaStatus[]> {
    return this.http.get<DeckMetaStatus[]>(
      buildUrl(`${this.basePath}/meta/${deckId}`, {})
    );
  }
}
