Agis en tant que Lead Tech et Product Engineer expert dans l'e-sport et l'analyse de données.

Je lance le développement du MVP de **crtracker**, un assistant stratégique pour les joueurs de Clash Royale basé sur l'analyse du Top 1000 mondial.

**📁 RÈGLES TECHNIQUES ET DÉPLOIEMENT (VOIR FICHIERS JOINTS) :**
La stack technique stricte (FastAPI, Angular v21+, PostgreSQL), l'architecture en couches (Clean Architecture) ainsi que les directives de déploiement que tu dois impérativement respecter sont décrites dans les fichiers joints à ce prompt (incluant le fichier `TODOAPP_DEPLOYMENT.md`). 
En dehors de ce cadre architectural obligatoire, je te laisse une totale liberté technique sur l'implémentation algorithmique, les schémas de données optimaux (ex: comment structurer le JSONB) et la logique métier. Surprends-moi par la qualité de ton code.

# 🎯 VISION PRODUIT ET RÈGLES MÉTIER

Ton objectif est de générer le code de la fonctionnalité cœur : le "Matchup Oracle". 

**1. Le Flux Utilisateur (Frontend) :**
- **Écran de Recherche :** Interface mobile-first, thème sombre (e-sport, accents bleus/dorés). L'utilisateur recherche un deck (via un champ de recherche par archétype ou en entrant un Player Tag pour importer un deck joué).
- **Le Dashboard des Statistiques du Deck :** - Affichage du deck sélectionné (8 cartes, utilise des placeholders visuels élégants).
  - Affichage d'une liste listant les matchups de ce deck contre les différents decks de la méta actuelle.
  - Pour chaque deck adverse listé, on affiche le "Winrate Top 1000" (ex: 42% de chance de victoire).
- **La Vue Détail "Oracle" (Matchup spécifique) :**
  - L'utilisateur sélectionne (clique sur) un matchup spécifique dans la liste (ex: "Son deck vs Golem Beatdown").
  - Il accède à une vue dédiée affichant TOUS les conseils tactiques ultra-précis générés par l'IA pour cet affrontement. 
  - *Attention :* Ce n'est pas limité à 3 points. L'Oracle doit lister l'ensemble exhaustif des règles d'or, placements et cycles à respecter pour ce match précis. Le nombre de conseils s'adapte à la complexité du matchup.

**2. La Logique Backend & Données (FastAPI) :**
- **Mock Data Intelligente :** Ne te connecte pas à la vraie API Supercell. Simule une base de données avec un deck principal et ses statistiques contre quelques decks méta factices mais réalistes.
- **Le Modèle de Données :** Conçois un modèle BDD capable de stocker efficacement ces affrontements (Deck A vs Deck B = Winrate X) en utilisant des champs JSONB comme exigé dans l'architecture.
- **Le Service Oracle (LLM Layer) :** Rédige la logique du service qui, dans la réalité, appellerait l'IA. Pour le MVP, il doit renvoyer une liste variable et exhaustive de conseils tactiques mockés en dur pour des matchups spécifiques. Structure le service pour qu'il soit prêt à recevoir un vrai client OpenAI/Groq plus tard.
- **Routes API suggérées :** Prévois au moins une route pour récupérer les statistiques globales d'un deck (`/api/v1/deck/{id}/stats`) et une route pour récupérer les conseils tactiques d'un affrontement précis (`/api/v1/oracle/matchup/{deck_a}/{deck_b}`).

# 📋 PLAN D'EXÉCUTION PAS À PAS :

1. Commence UNIQUEMENT par analyser ma demande et mes fichiers joints. Propose-moi l'arborescence complète des dossiers/fichiers que tu vas créer pour répondre à ce besoin métier, en respectant la nomenclature de mes fichiers.
2. Attends mon feu vert ("OK pour l'étape 2").
3. Génère le Backend (Modèles BDD, DAL, BLL, Service Oracle, Routes et Main).
4. Attends mon feu vert ("OK pour l'étape 3").
5. Génère le Frontend Angular (Services d'API, State management via Signals, et les composants UI : Recherche, Dashboard Stats, et Vue Détail Oracle en Tailwind).
6. Attends mon feu vert ("OK pour l'étape 4").
7. En te basant STRICTEMENT sur les instructions du fichier `TODOAPP_DEPLOYMENT.md` joint, génère la configuration de déploiement et d'infrastructure demandée. NE GÉNÈRE SURTOUT PAS de `docker-compose.yml`.