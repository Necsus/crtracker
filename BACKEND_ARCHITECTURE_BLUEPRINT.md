# 🏗️ Architecture Backend (FastAPI) - Blueprint Détaillé

Ce document détaille l'architecture stricte en couches (Clean Architecture) utilisée pour le développement du Backend Python. Il doit servir de guide absolu pour l'ajout de nouvelles fonctionnalités et pour la génération de code par des LLMs.

## 1. Stack Technique
- **Framework Principal** : FastAPI (`fastapi`, `uvicorn[standard]`)
- **Langage** : Python 3.10+ (Typage strict requis)
- **Base de données & ORM** : PostgreSQL, SQLAlchemy 2.0 (en mode natif asynchrone `asyncpg`)
- **Migrations** : Alembic
- **Validation des données** : Pydantic (v2) et Pydantic-Settings
- **Sécurité** : JWT (`python-jose`), hachage de mots de passe (`bcrypt`)

---

## 2. Le Modèle en Couches (Layered Architecture)

L’arborescence est prefixée par des lettres (`a_`, `b_`, etc.) pour forcer un ordre visuel et respecter la direction des dépendances. Une couche supérieure peut appeler une couche inférieure, mais l'inverse est **strictement interdit**.

### `b_models/` (Couche Données - Entités ORM)
- **Rôle** : Reflète exclusivement le schéma de la base de données.
- **Règles** :
  - Hérite de la classe `Base` de SQLAlchemy.
  - Ne contient **aucune logique métier**.
  - Utilise les types abstraits de SQLAlchemy 2.0 (`Mapped`, `mapped_column`).
  - Utilise intensivement les champs de type `JSONB` pour stocker des listes complexes sans multiplier les tables relationnelles.

### `a_dal/` (Couche d'Accès aux Données - Data Access Layer)
- **Rôle** : Isoler toutes les requêtes SQL (sélection, insertion, mise à jour, suppression) hors du reste de l'application.
- **Règles** :
  - Hérite généralement d'un `BaseDAL` exposant les méthodes CRUD génériques.
  - Reçoit la session de la base de données (`AsyncSession`) lors de son initialisation.
  - **Ne connaît pas HTTP** (ne soulève pas d'exceptions HTTP `HTTPException`).
  - Toute action vers PostgreSQL doit passer par ici, de façon 100% asynchrone.

### `c_bll/` (Couche Métier - Business Logic Layer)
- **Rôle** : Contient le cœur de la logique de l'application (Services).
- **Règles** :
  - Instancie et utilise les classes du `a_dal/`.
  - Applique les règles de gestion (autorisation de suppression, calculs complexes, enrichissement de données).
  - Gère les exceptions métier.
  - Ne manipule pas directement les requêtes HTTP (ni Request, ni Response).

### `d_llm/` ou autres (Couche Intégrations / Providers externes)
- **Rôle** : Encapsuler la logique des appels vers des APIs tierces (ex: Groq, OpenAI, Services externes).
- **Règles** :
  - Fournit des interfaces ou des classes de services utilisables par la BLL.

### `routes/` (Couche Interface / Controllers)
- **Rôle** : Gérer les requêtes et réponses HTTP liées au framework FastAPI.
- **Règles** :
  - Déclare les endpoints via les `APIRouter`.
  - Effectue la conversion/validation grâce aux `schemas.py` de Pydantic.
  - Utilise l'Injection de Dépendances de FastAPI (`Depends`) pour récupérer la session DB système et instancier les services de la BLL.
  - Gère les codes de statut HTTP et renvoie structurées les erreurs (`HTTPException`).
  - Les fichiers doivent se nommer avec le suffixe `_route.py` (ex: `users_route.py`).

---

## 3. Composants Périphériques Transverses

- **`schemas.py` (DTOs)** : Définit les modèles d'entrée (Request) et de sortie (Response) grâce à Pydantic. Pydantic valide, caste et documente (via OpenAPI) la donnée avant même qu'elle n'atteigne vos routes. Permet de disjoindre la structure des tables SQL de ce qui est réellement exposé via l'API.
- **`database.py`** : Définit l'Engine asynchrone SQLAlchemy et la fabrique de session (`async_sessionmaker`). Fournit le générateur `get_db()` utilisé pour l'Injection de Dépendance.
- **`config.py`** : Gère les variables d'environnement centralisées et typées via `pydantic-settings` (ex: `DATABASE_URL`, `SECRET_KEY`).
- **`main.py`** : Point d'entrée de Uvicorn. Initialise l'application FastAPI, configure les middlewares (CORS), et inclut (`include_router()`) tous les routers de la couche `routes/`.

---

## 4. Arborescence Cible

```text
backend/
├── alembic.ini              # Fichier de config pour les migrations ORM
├── requirements.txt         # Dépendances du projet
├── alembic/                 # Scripts générés de migration BDD
└── app/
    ├── __init__.py
    ├── config.py            # Settings (Pydantic BaseSettings)
    ├── database.py          # Session, Engine & Base SQLAlchemy
    ├── main.py              # Application FastAPI & CORS
    ├── schemas.py           # DTOs (Data Transfer Objects) Pydantic
    ├── a_dal/               # DAL
    │   ├── base_dal.py      # Base générique pour le CRUD
    │   └── example_dal.py   # Ex: user_dal.py
    ├── b_models/            # SQLAlchemy Models
    │   └── example.py       # Ex: user.py
    ├── c_bll/               # Business Logic Services
    │   └── example_service.py # Ex: user_service.py
    ├── d_llm/               # (Optionnel) Intégrations abstraites
    │   └── provider_client.py 
    └── routes/              # Controllers API
        └── examples_route.py  # Ex: users_route.py
```

---

## 💡 Prompt d'Initialisation Backend (LLM)

Pour générer un nouveau backend (ou ajouter une feature sur un existant) via une IA, ajoutez ceci à votre prompt :

> *"Je souhaite générer la structure et le code d'un backend en Python / FastAPI nommé <strong>[Nom]</strong>, ou y ajouter la fonctionnalité <strong>[Nom Feature]</strong>. Tu vas strictement respecter le pattern 'Clean Architecture' suivant les dossiers et préfixes: `b_models/` (SQLAlchemy 2 async), `schemas.py` (Pydantic v2), `a_dal/` (Hérite du BaseDAL, interagit avec la session async), `c_bll/` (Logique métier orchestrant le DAL), et `routes/` (APIRouter FastAPI avec le suffixe _route.py).
> Implémente toutes ces couches pour la gestion de l'entité <strong>[Nom Entité]</strong>. La fonction HTTP finale (dans `routes/`) doit utiliser l'injection de dépendances (`Depends`) de FastAPI pour instancier la BLL qui instancie le DAL avec l'AsyncSession DB. Ne fournis aucun code pour le Frontend en réponse."*