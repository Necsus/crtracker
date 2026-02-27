# 🏗️ Architecture Frontend (Angular) - Blueprint Détaillé

Ce document détaille l'architecture utilisée pour le développement du Frontend Angular (SPA). Il s'agit d'une architecture orientée "Features" associée à un partitionnement fort des responsabilités technique (DAL, BLL, UI) et privilégiant la **réactivité moderne via les Signals d'Angular**.

## 1. Stack Technique
- **Framework** : Angular v21+
- **Paradigme** : Architecture exclusivement **Standalone Components** (plus de `NgModules` globaux) et **Control Flow** moderne (`@if`, `@for`).
- **Langage** : TypeScript 5.9+ (Mode strict activé)
- **State Management & Réactivité** : **Signals** (`signal()`, `computed()`, `effect()`) en priorité pour l'état local et partagé.
- **Réseau** : Appels HTTP via le `HttpClient` natif mixé avec **RxJS** (les Subjects et Observables sont cantonnés aux flux d'événements réseaux inter-services, transformés en Signals si possible pour la vue).
- **Rendu & UI** : SCSS (encapsulé par composant).

---

## 2. Philosophie et Structuration en Couches

A l'instar du backend, le code TypeScript est isolé en "layers" via des préfixes numériques ou par module métier.

### `00_dal/` (Data Access Layer - Intégration API backend)
- **Rôle** : Unique endroit autorisé à effectuer des requêtes `HttpClient` vers l'extérieur.
- **Règles** :
  - Comprend des services finissant par `.dal.ts`.
  - Mappe les URIs du backend de manière structurée.
  - Ne gère **aucun état local** (pas de stockage de la data récupérée). Retourne toujours des `Observable<T>`.
  - Comprend les intercepteurs (ex: `api.interceptor.ts`) qui traitent le rattachement de tokens et l'interception automatique d'erreurs (401, 500).

### `01_models/` (Couche des Typages)
- **Rôle** : Miroir exact des entités et DTOs provenant du backend (Schemas Pydantic du backend).
- **Règles** :
  - Uniquement des `interface`, `type`, et d'éventuels `enum`. Aucune logique d'exécution.
  - Fichiers nommés `*.model.ts`.

### `10_bll/` (Business Logic Layer - State Management & Services Front)
- **Rôle** : Piloter la logique applicative lourde, agréger les datas provenant de plusieurs instances `DAL` et exposer un état réactif unifié.
- **Règles** :
  - Injecte les classes du DAL.
  - Extrait et maintient l'état applicatif avec des **Signals**, exposés le plus souvent en `ReadonlySignal`.
  - Gère l'authentification côté client, la préparation des structures de données complexes avant envoi aux "Smart Components".

### `shared/` (UI Autonome & Utilitaires)
- **Rôle** : Composants de présentation pure ("Dumb Components"), Directives, Pipes et Utilitaires.
- **Règles** :
  - Les composants UI (boutons, cartes, modales, spinners) dépendent uniquement d'inputs (`@Input` ou la fonction signal `input()`) et d'outputs (`@Output()` ou `output()`).
  - Aucun lien direct avec la BLL ou le DAL. Ils n'ont pas conscience du domaine métier ou de la base de données.

### Dossiers `feature_xyz/` (Modules d'Interface Utilisateur)
- **Rôle** : Contient l'interface et la navigation liées à un segment fonctionnel de l'application (ex: `auth/`, `dashboard/`, `session/`).
- **Structure type d'une Feature** :
  - Fichier de routing (`feature.routes.ts`) contenant une constante typée `Routes`, chargée par le router global en `loadChildren`.
  - Composants intelligents ("Smart Components") qui s'injectent des BLL pour obtenir l'état et exécuter des actions, puis les passent aux composants `shared/` via l'HTML.

---

## 3. Arborescence Cible

```text
frontend/
├── angular.json
├── package.json
└── src/
    ├── index.html
    ├── main.ts              # Amorce Bootstrap (provideHttpClient, provideRouter)
    ├── styles.scss          # CSS Global (Variables, couleurs, typographie)
    └── app/
        ├── 00_dal/          # Appels HTTP backend
        │   ├── api.interceptor.ts
        │   └── example.dal.ts
        ├── 01_models/       # Typages stricts (miroirs du backend)
        │   └── example.model.ts
        ├── 10_bll/          # Business Logic (Gestion Signal / État)
        │   └── example.service.ts
        ├── shared/          # UI pur, components Dumb, Pipes
        │   └── components/
        │       └── custom-button/
        ├── example-feature/ # Exemple: auth/
        │   ├── example-list.component.ts
        │   ├── example-detail.component.ts
        │   └── example.routes.ts
        ├── app.component.ts # Root (router-outlet principal)
        ├── app.config.ts    # Providers application (Interceptor, animations, routeur)
        └── app.routes.ts    # Routage paresseux vers les Features
```

---

## 4. Règles Architecturales Modernes d'Angular 21+
- Remplacer les classes décorées `@Component` avec `inputs` traditionnels par le système `input()` via les API de Signaux afin que le ChangeDetection s'optimise par défaut ("Zoneless" ready).
- Utiliser le constructeur paramétré (`inject()`) au lieu du constructeur classique si c'est plus lisible, bien que les deux soient acceptés.
- Les interactions dans le template utiliseront le control flow Angular moderne :
  - `@if (stateSignal(); as state)` au lieu de `*ngIf`.
  - `@for (item of items(); track item.id)` au lieu de `*ngFor`.
- Utilisation de **Pipes Purs** pour transformer les données dans le template (ex: Parsing Markdown, Dates) pour éviter de recalculer inutilement.

---

## 💡 Prompt d'Initialisation Frontend (LLM)

Pour générer une nouvelle application (ou une feature sur le frontend) via une IA, ajoutez ceci à votre prompt :

> *"Je souhaite concevoir l'interface d'une application Angular v21+ (ou développer la feature <strong>[Nom Feature]</strong>). Code en utilisant l'architecture strictement typée suivante : `00_dal/` (Composé uniquement d'appels HTTP retournant des Observables, nommé `.dal.ts`), `01_models/` (Interfaces TypeScript), `10_bll/` (Services gérant la logique métier et le state management en exposant des Signals `signal<T>`, et appelant le DAL), et des dossiers Features (`feature_name/`) contenant des Standalone Components avec le Control Flow moderne (`@if`, `@for`). Favorise l'utilisation de `inject()` et la nouvelle API Signal (`input()`, `computed()`) pour les inputs des composants. Déploie une séparation nette entre "Smart Components" et "Dumb Components". Ne fournis aucun code backend dans ta réponse."*