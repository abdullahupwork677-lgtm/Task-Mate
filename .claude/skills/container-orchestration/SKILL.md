---
name: container-orchestration
description: Complete container orchestration with 8 commands - Kubernetes deployment (Deployment/Service/Ingress/HPA), Helm chart packaging, Docker multi-stage builds (Python FastAPI + Next.js), health checks (liveness/readiness), resource limits, auto-scaling, and Docker Compose. Use when containerizing applications for production Kubernetes without DevOps expertise (70-80% time savings, includes Phase 4 learnings).
---

# Container Orchestration

**Production Kubernetes deployment - No DevOps expertise needed!**

**Category:** Containerization & Orchestration
**Time Savings:** 70-80% reduction
**Quality:** Production-ready with health checks

---

## 📋 Quick Instructions

1. **Create K8s Manifests**
   ```bash
   python3 scripts/tool.py create-manifests --app myapp
   ```

2. **Build Docker Images**
   ```bash
   python3 scripts/tool.py build-images
   ```

3. **Deploy to Kubernetes**
   ```bash
   python3 scripts/tool.py deploy --namespace production
   ```

4. **Verify Deployment**
   ```bash
   python3 scripts/tool.py health-check
   ```

---

## 🛠️ Commands (8 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py check-prerequisites
python3 scripts/tool.py create-manifests --app myapp
python3 scripts/tool.py build-images
python3 scripts/tool.py deploy --namespace production
python3 scripts/tool.py scale --replicas 5
python3 scripts/tool.py health-check
python3 scripts/tool.py troubleshoot
python3 scripts/tool.py test
```

---

## 📁 On-Demand Resources

### Kubernetes Manifests
- **Directory:** `assets/k8s/`
- **When:** Deploying to Kubernetes
- **Contains:** Deployment, Service, Ingress, HPA YAML templates

### Docker Multi-Stage Builds
- **File:** `reference/docker-multistage.md`
- **When:** Building production images
- **Contains:** FastAPI (Python 3.13), Next.js (Node 20), best practices

### Health Check Patterns
- **File:** `reference/health-checks.md`
- **When:** Implementing liveness/readiness
- **Contains:** /health (liveness), /ready (readiness with DB check)

### Helm Charts
- **Directory:** `assets/helm/`
- **When:** Packaging applications
- **Contains:** Chart.yaml, values.yaml templates

### Docker Compose
- **File:** `examples/docker-compose.yml`
- **When:** Local development
- **Contains:** Multi-service setup with health checks

### Phase 4 Learnings
- **File:** `reference/phase4-learnings.md`
- **When:** Production deployment
- **Contains:** Standalone output, non-root user, HEALTHCHECK

---

## 🚀 Common Workflows

### Workflow 1: Full Deployment
```bash
1. python3 scripts/tool.py check-prerequisites
2. python3 scripts/tool.py create-manifests --app myapp
3. python3 scripts/tool.py build-images
4. python3 scripts/tool.py deploy --namespace production
5. python3 scripts/tool.py health-check
```

### Workflow 2: Docker Compose Local
```bash
1. python3 scripts/tool.py build-images
2. docker-compose up -d
```

---

## 💡 Token Efficiency

**Before:** 345 lines
**After:** ~125 lines
**Savings:** 64% reduction ✅

---

**Status:** Production-ready ✅
**Phase 4 learnings included!** 🚀
