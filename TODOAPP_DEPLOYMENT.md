# 🚀 Architecture de Déploiement : Kubernetes & CI/CD (TODOAPP)

Ce document décrit en détail l'infrastructure technique requise pour déployer **TODOAPP** sur un cluster Kubernetes (K3s) via une chaîne d'intégration et de déploiement continus (CI/CD) sur GitHub Actions.

---

## 🏗️ 1. Arborescence de déploiement

Le code gérant l'infrastructure se trouve dans deux répertoires principaux à la racine du projet :

```text
/
├── .github/
│   └── workflows/
│       └── deploy-app.yml         # Pipeline CI/CD GitHub Actions
└── k8s/
    ├── namespace.yaml             # Définition du namespace Kubernetes
    ├── ingress.yaml               # Routage Traefik & Certificats SSL
    ├── secrets-template.yaml      # Modèle pour les Secrets K8s
    ├── db-init-job.yaml           # Job de création de BDD / Migrations Alembic
    ├── backend/
    │   ├── deployment.yaml        # Déploiement de l'API FastAPI
    │   └── service.yaml           # Service interne port 8000
    └── frontend/
        ├── deployment.yaml        # Déploiement du front Angular/Nginx
        └── service.yaml           # Service interne port 80
```

---

## ☸️ 2. Configuration Kubernetes (`k8s/`)

L'application est cloisonnée dans son propre namespace et se compose de multiples ressources Kubernetes.

### a. Sécurité & Configuration (`namespace.yaml`, `secrets.yaml`)
- **Namespace** : Toute l'application tourne dans le namespace `todoapp`.
- **Secrets Kubernetes** : Les clés API (LLM, Auth, etc.) et les chaînes de connexion à la base de données (PostgreSQL) sont injectées en tant que variables d'environnement dans le cluster. Un `imagePullSecret` nommé `registry-credentials` est également utilisé pour s'authentifier auprès du registre Docker privé.

### b. Base de Données & Migrations (`db-init-job.yaml` ou InitContainers)
Avant, ou pendant le démarrage de l'API, des **Jobs Kubernetes** (ou *initContainers*) exécutent les scripts de migration de schémas.
Le conteneur backend exécute la commande `alembic upgrade head` contre la base de données `todoapp_db` via `DATABASE_URL` pour s'assurer que le schéma SQL correspond parfaitement à la version du code déployé.

### c. Frontend Angular (`k8s/frontend/`)
- **Deployment** : Déploie l'image `registry.necsus.dev/todoapp/frontend:latest`. Le conteneur expose un serveur Nginx allégé (port 80) servant les fichiers distilés d'Angular. 
- **Service** : Redirige le trafic interne du cluster vers les pods Nginx.

### d. Backend FastAPI (`k8s/backend/`)
- **Deployment** : Déploie l'image `registry.necsus.dev/todoapp/backend:latest`. L'API tourne sur Uvicorn (port 8000). Le manifeste YAML mape toutes les variables d'environnement nécessaires (ex: `APP_NAME`, `DATABASE_URL`, `SECRET_KEY`) depuis les `Secrets`.
- **Service** : Redirige le trafic interne vers l'API.

### e. Ingress & Routage Externe (`k8s/ingress.yaml`)
L'Ingress gère le trafic entrant via l'IngressController **Traefik** couplé à **Cert-Manager** pour la génération automatique de certificats TLS vi Let's Encrypt.
- Le sous-domaine `todoapp.necsus.dev` est routé vers le `Service` **frontend**.
- Le sous-domaine `api-todoapp.necsus.dev` est routé vers le `Service` **backend**.

---

## ⚙️ 3. Intégration et Déploiement Continus (`.github/workflows/deploy-app.yml`)

La CI/CD est automatisée via **GitHub Actions**. Le workflow se déclenche sur push (ex: sur la branche `recette` ou `main`) ou manuellement (`workflow_dispatch`).

Le pipeline est divisé en **deux jobs consécutifs** :

### Job 1 : `build-and-push`
1. **Checkout du code** : Récupère les sources depuis GitHub.
2. **Setup Docker Buildx** : Active le moteur de build avancé pour gérer le cache de l'image.
3. **Login Registre Privé** : S'authentifie sur `registry.necsus.dev` via les `secrets` configurés sur GitHub.
4. **Génération des Tags** : Crée un tag avec le Commit SHA court et `latest` (ex: `registry.necsus.dev/todoapp/frontend:latest`).
5. **Build & Push (Frontend + Backend)** :
   - Construit les images Docker définies par les `Dockerfile` respectifs.
   - Pousse (Push) ces images sur le registre.
   - Gère le cache de build Docker pour réduire la durée des pipelines suivants.

### Job 2 : `deploy`
1. **Connexion VPN (Optionnel/Sécurité)** : Utilise souvent de quoi connecter le runner GitHub au cluster sécurisé. Dans notre cas, **Tailscale** est utilisé en tant qu'action GitHub pour accéder à l'IP privée du `Control Plane` du cluster K3s.
2. **Configuration Kubectl** : Télécharge le contexte (`KUBECONFIG`) injecté par GitHub Secrets et poinçonne la bonne adresse IP locale (ex: `100.108.255.93`).
3. **Initialisation K8s** : 
   - Crée le namespace `todoapp` via `kubectl apply -f k8s/namespace.yaml`.
   - Charge ou met à jour les identifiants d'accès au Docker Registry local (création du secret de type `docker-registry`).
   - Pousse les variables d'environnement (Base de TDD, Tokens) vers les *Secrets* de `todoapp`.
4. **Déploiement K8s** : 
   - Applique les manifests (`kubectl apply -f k8s/` ou via kustomize/helm).
   - Met à jour l'image des déploiements spécifiquement avec le `--image=...:SHORT_SHA` fraichement buildé si besoin, ou redémarre le déploiement (`kubectl rollout restart deployment backend -n todoapp`).

---

## 💡 Prompt d'Initialisation DevOps (Pour une IA)

Si vous voulez qu'un assistant IA vous génère l'infrastructure pour **TODOAPP** :

> *"Je développe une application **TODOAPP** composée d'un backend FastAPI et d'un frontend Angular qui sera déployée sur un cluster Kubernetes (K3s, controller Ingress Traefik). Créé-moi l'ensemble des manifestes Kubernetes (`k8s/`) incluant un `namespace.yaml`, `ingress.yaml` (utilisant cert-manager let's encrypt pour todoapp.exemple.com), et les dossiers `backend/` et `frontend/` avec leurs `deployment` et `service` respectifs.*
>
> *Ensuite, génère-moi le fichier de CI/CD `.github/workflows/deploy-app.yml` qui build les deux images Docker, les push sur mon registre privé, configure Tailscale et kubectl, puis applique automatiquement mes manifestes k8s dans le namespace `todoapp`."*