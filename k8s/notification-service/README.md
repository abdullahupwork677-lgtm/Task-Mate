# Notification Service Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the notification service with full production configuration.

## 📦 Manifests Overview

### Core Resources (T164-T168)

| File | Resource | Purpose |
|------|----------|---------|
| `deployment.yaml` | Deployment | 3 replicas with resource limits, health checks |
| `service.yaml` | Service | ClusterIP service on port 8080 |
| `configmap.yaml` | ConfigMap | Kafka servers, topic names, email config |
| `secrets.yaml` | Secret | SendGrid API key, Firebase credentials, DB URL |
| `hpa.yaml` | HorizontalPodAutoscaler | Auto-scale 3-10 replicas based on CPU/memory |

### Dapr Components (T169-T173)
- `dapr-components/cron-binding.yaml` - Dapr cron for periodic reminder checks
- `dapr-components/kafka-pubsub.yaml` - Dapr Kafka pub/sub component
- `dapr-components/secrets-store.yaml` - Dapr Kubernetes secrets integration

---

## 🚀 Quick Deployment

### Step 1: Configure Secrets (REQUIRED)

**Edit `secrets.yaml` with base64-encoded values:**

```bash
# SendGrid API Key
echo -n "SG.your-sendgrid-api-key" | base64

# Firebase Service Account (JSON file)
cat firebase-service-account.json | base64 -w 0

# Database URL
echo -n "postgresql://user:password@host:5432/database" | base64
```

Replace placeholders in `secrets.yaml`:
- `<BASE64_ENCODED_SENDGRID_API_KEY>`
- `<BASE64_ENCODED_FIREBASE_CREDENTIALS_JSON>`
- `<BASE64_ENCODED_DATABASE_URL>`

### Step 2: Update ConfigMap (Optional)

Edit `configmap.yaml` to customize:
- Kafka bootstrap servers
- Email sender details
- Log level

### Step 3: Apply Manifests

```bash
# Apply all manifests
kubectl apply -f k8s/notification-service/

# Verify deployment
kubectl get pods -l app=notification-service
kubectl get svc notification-service
kubectl get hpa notification-service-hpa
```

---

## 🔍 Deployment Verification

### Check Pod Status

```bash
# List pods
kubectl get pods -l app=notification-service

# Expected output: 3 pods running
# NAME                                    READY   STATUS    RESTARTS   AGE
# notification-service-<hash>-xxxxx       1/1     Running   0          2m
# notification-service-<hash>-yyyyy       1/1     Running   0          2m
# notification-service-<hash>-zzzzz       1/1     Running   0          2m
```

### Check Service

```bash
kubectl get svc notification-service

# Expected output:
# NAME                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
# notification-service   ClusterIP   10.96.x.x      <none>        8080/TCP   2m
```

### Check HPA

```bash
kubectl get hpa notification-service-hpa

# Expected output:
# NAME                       REFERENCE                       TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# notification-service-hpa   Deployment/notification-service   15%/80%   3         10        3          2m
```

### Check Logs

```bash
# Tail logs from all pods
kubectl logs -l app=notification-service -f

# Check specific pod
kubectl logs notification-service-<hash>-xxxxx -f
```

---

## 🔧 Configuration Details

### Resource Limits (T164)

```yaml
resources:
  requests:
    cpu: 100m      # 0.1 CPU cores
    memory: 256Mi  # 256 MB
  limits:
    cpu: 500m      # 0.5 CPU cores
    memory: 512Mi  # 512 MB
```

**Recommendation:**
- Development: Use requests as shown
- Production: Increase based on load testing results

### Auto-Scaling (T168)

```yaml
minReplicas: 3
maxReplicas: 10
targetCPUUtilization: 80%
targetMemoryUtilization: 80%
```

**Scaling Behavior:**
- **Scale Up**: Immediate (0s stabilization)
  - Add up to 100% of current replicas every 30s
  - Or add up to 2 pods every 30s
- **Scale Down**: Gradual (5 min stabilization)
  - Remove up to 50% of current replicas every 60s
  - Or remove up to 1 pod every 60s

### Health Checks

```yaml
livenessProbe:
  initialDelaySeconds: 30  # Wait 30s before first check
  periodSeconds: 10        # Check every 10s
  failureThreshold: 3      # Restart after 3 failures

readinessProbe:
  initialDelaySeconds: 10  # Ready check starts at 10s
  periodSeconds: 5         # Check every 5s
  failureThreshold: 3      # Mark unhealthy after 3 failures
```

---

## 🐞 Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod notification-service-<hash>-xxxxx

# Common issues:
# 1. ImagePullBackOff: Image doesn't exist
# 2. CrashLoopBackOff: Application error
# 3. Pending: Insufficient resources
```

### Secret Decoding Errors

```bash
# Verify secret is base64 encoded
kubectl get secret notification-service-secrets -o yaml

# Decode to verify
kubectl get secret notification-service-secrets -o jsonpath='{.data.sendgrid-api-key}' | base64 -d
```

### Kafka Connection Issues

```bash
# Check Kafka connectivity from pod
kubectl exec -it notification-service-<hash>-xxxxx -- sh
# Inside pod:
nc -zv redpanda 9092
```

### Health Check Failures

```bash
# Test health endpoint
kubectl exec -it notification-service-<hash>-xxxxx -- curl http://localhost:8080/health

# Expected response:
# {"status": "healthy", "kafka": "connected", "database": "connected"}
```

---

## 📊 Monitoring

### CPU/Memory Usage

```bash
# Real-time resource usage
kubectl top pods -l app=notification-service

# Expected output:
# NAME                                   CPU(cores)   MEMORY(bytes)
# notification-service-<hash>-xxxxx      50m          200Mi
# notification-service-<hash>-yyyyy      45m          195Mi
# notification-service-<hash>-zzzzz      48m          198Mi
```

### HPA Status

```bash
# Watch HPA in real-time
kubectl get hpa notification-service-hpa --watch

# If CPU usage > 80%, HPA will add replicas
# If CPU usage < 80% for 5 minutes, HPA will remove replicas
```

---

## 🔄 Rolling Updates

```bash
# Update image version
kubectl set image deployment/notification-service notification-service=notification-service:v2

# Watch rollout status
kubectl rollout status deployment/notification-service

# Rollback if issues
kubectl rollout undo deployment/notification-service
```

---

## 🧹 Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/notification-service/

# Or delete individual resources
kubectl delete deployment notification-service
kubectl delete service notification-service
kubectl delete hpa notification-service-hpa
kubectl delete configmap notification-service-config
kubectl delete secret notification-service-secrets
```

---

## 📚 Next Steps

After deploying:

1. **T169-T173**: Add Dapr components for cron and Kafka
2. **T174-T176**: Create Helm chart for easier deployment
3. **T177-T180**: Test full notification flow
4. **Phase 11**: Add observability (logging, metrics, health checks)

---

**Status**: ✅ T164-T168 Complete (Kubernetes Manifests)
**Production Ready**: Requires secrets configuration
**Estimated Setup Time**: 15-20 minutes
