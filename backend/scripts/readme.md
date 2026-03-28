# Scripts — CRTracker Backend

Tous les scripts s'exécutent depuis le répertoire **`backend/`** avec le virtualenv activé.

```bash
cd backend
source .venv/bin/activate  # Windows : .venv\Scripts\Activate.ps1
```

---

## seed_archetypes.py 🏷️ Archetypes indemodables

Peuple la table `archetypes` avec les archétypes *indemodables* (timeless) : Hog 2.6, Log Bait, X-Bow 3.0, etc.

**Ordre recommandé d'exécution :**
```
alembic upgrade head          # migration 006 (tables archetypes + deck_meta_statuses)
python -m scripts.sync_cards  # remplir la table cards pour la résolution des IDs
python -m scripts.seed_archetypes --commit
```

```bash
# Aperçu sans écriture (dry-run par défaut)
python -m scripts.seed_archetypes

# Écriture effective en base
python -m scripts.seed_archetypes --commit
```

**Archetypes seedés :**

| Famille | Variantes timeless |
|---|---|
| Hog Cycle | Hog 2.6, Hog 3.0 |
| Log Bait | Log Bait Classic |
| X-Bow Siege | X-Bow 3.0, X-Bow 4.0 |
| Mortar Cycle | — |
| Golem Beatdown | Golem Night Witch, Golem Lumberjack |
| LavaLoon | LavaLoon Tombstone, LavaLoon Freeze |
| Miner Control | Miner Poison Gang |
| Graveyard Control | Graveyard Poison |
| PEKKA Bridge Spam | Classic PEKKA BS |
| Giant Beatdown | Giant Double Prince |

**Résolution des card IDs :** le script traduit les noms de cartes lisibles ("Hog Rider") vers l'`id` numérique CR API stocké dans `decks.cards[].id`.  Si la table `cards` est vide (environnement mock), il utilise un slug kebab-case comme fallback (`hog-rider`).

**Idempotent :** peut être relancé sans créer de doublons (upsert par `name`).

---

## sync_top1000.py ✨ Recommandé

Pipeline complet en une seule commande : classement → profils → battlelogs → decks.

**Ce que ça fait (dans l'ordre) :**
1. Récupère le top-N du classement global Path of Legend
2. Pour chaque joueur, récupère **en parallèle** son profil complet + son battlelog
3. Upsert tous les profils dans la table `players`
4. Upsert toutes les batailles dans la table `battles` (`ON CONFLICT DO NOTHING`)
5. Agrège les decks **uniquement depuis les batailles `pathOfLegend`** et les upsert dans `decks`

```bash
# Top 1000 complet (saison courante) — utilisation type
python -m scripts.sync_top1000

# Taille personnalisée
python -m scripts.sync_top1000 --top 200

# Saison spécifique
python -m scripts.sync_top1000 --top 1000 --season 2026-02

# Contrôle de la concurrence et du seuil de bruit
python -m scripts.sync_top1000 --concurrency 8 --min-count 3
```

| Option | Défaut | Description |
|---|---|---|
| `--top` | 1000 | Nombre de joueurs à synchoniser |
| `--season` | mois courant | Saison au format `YYYY-MM` |
| `--concurrency` | 10 | Requêtes API simultanées |
| `--min-count` | 2 | Apparitions minimum pour stocker un deck |
| `--batch-size` | 100 | Taille des batches d'écriture en DB |

> Remplace le workflow en 3 étapes (`sync_players` → `sync_battles` → `extract_decks`).
> Utilisez les scripts individuels uniquement si vous avez besoin d'une étape spécifique
> (ex. : rafraîchir les cartes avec `sync_cards`, ou expansion récursive des adversaires avec `sync_battles --depth 1`).

---

## sync_players.py

Synchronise les joueurs Path of Legend depuis l'API Clash Royale vers la table `players`.

**Ce que ça fait :**
1. Récupère le classement global Path of Legend (`/v1/locations/global/pathoflegend/{season}/rankings/players`)
2. Récupère le profil complet de chaque joueur (`/v1/players/{tag}`)
3. Upsert dans la table `players` (mise à jour si déjà présent)

```bash
# Top 1000 (saison courante)
python -m scripts.sync_players

# Top 200 uniquement
python -m scripts.sync_players --top 200

# Saison spécifique
python -m scripts.sync_players --top 1000 --season 2026-02

# Contrôle de la concurrence (défaut : 10)
python -m scripts.sync_players --concurrency 5
```

---

## sync_battles.py

Synchronise les batalles depuis les logs des joueurs vers la table `battles`.

**Ce que ça fait :**
1. Récupère le top-N du classement Path of Legend pour obtenir les tags
2. Pour chaque tag, récupère les 25 derniers matchs (`/v1/players/{tag}/battlelog`)
3. Normalise chaque bataille (clé déterministe → pas de doublons)
4. Expansion récursive optionnelle : récupère aussi les batailles des adversaires rencontrés
5. Upsert avec `ON CONFLICT DO NOTHING` — relançable sans risque

```bash
# Top 1000 (défaut)
python -m scripts.sync_battles

# Top 200 seulement
python -m scripts.sync_battles --top 200

# Saison spécifique
python -m scripts.sync_battles --top 1000 --season 2026-02

# Récursif : top 200 + adversaires (profondeur 1)
python -m scripts.sync_battles --top 200 --depth 1

# Profondeur 2 (adversaires des adversaires) — beaucoup de données
python -m scripts.sync_battles --top 100 --depth 2

# Leaderboard EU par location ID
python -m scripts.sync_battles --top 500 --location 57000094
```

---

## sync_cards.py

Synchronise le catalogue de cartes depuis l'API officielle et `cr-api-data`.

**Ce que ça fait :**
1. Récupère `GET /v1/cards` (icônes, niveaux, rareté)
2. Récupère les métadonnées complémentaires depuis `royaleapi.github.io/cr-api-data` (type, description, arène)
3. Insère les nouvelles cartes, met à jour les existantes (matchées par `card_id`)

À relancer après chaque mise à jour du jeu.

```bash
python -m scripts.sync_cards

# Avec un token explicite
CR_API_TOKEN=<token> python -m scripts.sync_cards
```

---

## extract_decks.py

Extrait les decks uniques des batailles enregistrées et les upsert dans la table `decks`.

**Ce que ça fait :**
1. Lit toutes les batailles en mémoire par batch
2. Extrait les 8 cartes de chaque équipe et les déduplique par clé sha1(cartes triées)
3. Agrège par deck : `plays`, `wins`, `global_winrate`
4. Filtre les decks sous le seuil `--min-count`
5. Upsert dans `decks` avec nom et archétype auto-générés

**Archetypes auto-détectés :** Cycle (`avg_elixir < 2.9`), Midladder (`< 3.5`), Beatdown (`≥ 7 elixir`), Control (reste)

```bash
# Tous les types de bataille
python -m scripts.extract_decks

# Seulement les batailles Path of Legend
python -m scripts.extract_decks --battle-type pathOfLegend

# Filtre bruit : minimum 3 apparitions
python -m scripts.extract_decks --min-count 3
```

---

## Ordre d'exécution recommandé

### Méthode rapide (une commande)

```bash
python -m scripts.sync_cards      # 1. Catalogue de cartes (à faire 1×)
python -m scripts.sync_top1000    # 2. Tout le reste en une passe
```

### Méthode détaillée (scripts individuels)

```bash
python -m scripts.sync_players    # 1. Joueurs
python -m scripts.sync_cards      # 2. Cartes
python -m scripts.sync_battles    # 3. Batailles
python -m scripts.extract_decks   # 4. Decks agrégés
```
