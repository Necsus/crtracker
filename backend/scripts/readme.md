# Top 1000 (défaut)
python -m scripts.sync_battles

# Top 200 seulement
python -m scripts.sync_battles --top 200

# Récursif : top 200 + adversaires de leurs matchs (profondeur 1)
python -m scripts.sync_battles --top 200 --depth 1

# Profondeur 2 (adversaires des adversaires) — beaucoup de données
python -m scripts.sync_battles --top 100 --depth 2

# Leaderboard EU par location ID
python -m scripts.sync_battles --top 500 --location 57000094