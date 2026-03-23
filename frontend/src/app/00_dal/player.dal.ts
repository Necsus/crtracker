import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  PlayerDetail,
  PlayerSearchResponse,
  PlayerTopResponse,
} from '../01_models/player.model';

@Injectable({ providedIn: 'root' })
export class PlayerDal {
  private http = inject(HttpClient);

  listTop(page = 1, pageSize = 20): Observable<PlayerTopResponse> {
    const params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);
    return this.http.get<PlayerTopResponse>('/api/v1/players', { params });
  }

  search(query: string): Observable<PlayerSearchResponse> {
    const params = new HttpParams().set('q', query);
    return this.http.get<PlayerSearchResponse>('/api/v1/players/search', { params });
  }

  getPlayer(tag: string): Observable<PlayerDetail> {
    return this.http.get<PlayerDetail>(`/api/v1/players/${encodeURIComponent(tag)}`);
  }
}
