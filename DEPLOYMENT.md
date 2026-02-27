# CRTracker Deployment Guide

This document covers the deployment of CRTracker on Kubernetes (K3s) using GitHub Actions CI/CD.

## Prerequisites

- K3s cluster with Traefik Ingress Controller
- Cert-Manager installed for Let's Encrypt SSL
- Tailscale for secure VPN access
- Private Docker registry (`registry.necsus.dev`)
- PostgreSQL database (can be external or in-cluster)

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository:

| Secret Name | Description |
|------------|-------------|
| `REGISTRY_USERNAME` | Docker registry username |
| `REGISTRY_PASSWORD` | Docker registry password |
| `KUBECONFIG` | Base64-encoded kubeconfig file |
| `TAILSCALE_OAUTH_CLIENT_ID` | Tailscale OAuth client ID |
| `TAILSCALE_OAUTH_CLIENT_SECRET` | Tailscale OAuth client secret |

### Generate kubeconfig secret

```bash
cat ~/.kube/config | base64 -w 0
```

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Configure Secrets

Edit `k8s/secrets-template.yaml` with actual values, then:

```bash
kubectl apply -f k8s/secrets-template.yaml
```

### 3. Deploy

Option A: Push to main branch (triggers CI/CD)

```bash
git push origin main
```

Option B: Manual workflow dispatch

```bash
gh workflow run deploy-app.yml
```

Option C: Manual deployment (skip CI)

```bash
# Apply manifests
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress.yaml

# Run migrations
kubectl apply -f k8s/db-init-job.yaml
kubectl wait --for=condition=complete job/db-migrate -n crtracker
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Traefik Ingress                           │
│                    (SSL via Cert-Manager)                    │
└─────────────────────────────────────────────────────────────┘
                    │                    │
        ┌───────────┴──────────┐        │
        ▼                      ▼        ▼
┌─────────────┐        ┌─────────────┐
│  Frontend   │        │   Backend   │
│  (Nginx)    │◄───────│   (FastAPI) │
│  Port: 80   │        │   Port: 8000│
└─────────────┘        └─────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │  (External DB)  │
                    └─────────────────┘
```

## URLs

- **Frontend**: https://crtracker.necsus.dev
- **Backend API**: https://api-crtracker.necsus.dev
- **API Docs**: https://api-crtracker.necsus.dev/docs (dev mode only)

## Troubleshooting

### View logs

```bash
# Backend logs
kubectl logs -n crtracker -l app=crtracker,component=backend -f

# Frontend logs
kubectl logs -n crtracker -l app=crtracker,component=frontend -f
```

### Check pod status

```bash
kubectl get pods -n crtracker
kubectl describe pod <pod-name> -n crtracker
```

### Restart deployments

```bash
kubectl rollout restart deployment/backend -n crtracker
kubectl rollout restart deployment/frontend -n crtracker
```

### Run migrations manually

```bash
kubectl delete job db-migrate -n crtracker
kubectl apply -f k8s/db-init-job.yaml
kubectl logs -n crtracker job/db-migrate -f
```

## Scaling

Manual scaling:

```bash
kubectl scale deployment/backend -n crtracker --replicas=4
kubectl scale deployment/frontend -n crtracker --replicas=3
```

The HPA (HorizontalPodAutoscaler) will auto-scale based on CPU usage:
- Backend: 2-10 replicas
- Frontend: 2-6 replicas

## Monitoring

The backend exposes Prometheus metrics on `/metrics`. Ensure Prometheus is configured to scrape:

```yaml
- job_name: 'crtracker-backend'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names: [crtracker]
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: crtracker
```
