# Notification Service Helm Chart

Official Helm chart for deploying the Todo App notification service with Kafka and Dapr.

## 📋 Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- Dapr 1.10+ installed in cluster
- Kafka/Redpanda cluster running

## 🚀 Installation

### Step 1: Configure Secrets

Edit `values.yaml` and replace the base64-encoded secret placeholders:

```bash
# SendGrid API Key
echo -n "SG.your-sendgrid-api-key" | base64

# Firebase Service Account JSON
cat firebase-service-account.json | base64 -w 0

# Database URL
echo -n "postgresql://user:password@host:5432/database" | base64
```

### Step 2: Install Chart (T176)

```bash
# Install with default values
helm install notification-service ./helm/notification-service

# Install with custom values
helm install notification-service ./helm/notification-service -f custom-values.yaml

# Install in specific namespace
helm install notification-service ./helm/notification-service --namespace todo-app --create-namespace
```

### Step 3: Verify Installation

```bash
# Check deployment status
kubectl get pods -l app.kubernetes.io/name=notification-service

# Check service
kubectl get svc -l app.kubernetes.io/name=notification-service

# Check HPA
kubectl get hpa -l app.kubernetes.io/name=notification-service
```

---

## ⚙️ Configuration

### Key Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `3` |
| `image.repository` | Image repository | `notification-service` |
| `image.tag` | Image tag | `latest` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `8080` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `256Mi` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |

### Autoscaling Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `true` |
| `autoscaling.minReplicas` | Minimum replicas | `3` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU threshold | `80` |
| `autoscaling.targetMemoryUtilizationPercentage` | Memory threshold | `80` |

### Kafka Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `kafka.bootstrapServers` | Kafka bootstrap servers | `redpanda:9092` |
| `kafka.consumerGroup` | Consumer group ID | `notification-service-group` |
| `kafka.remindersTopic` | Reminders topic name | `reminders` |
| `kafka.dlqTopic` | Dead letter queue topic | `reminders.dlq` |

### Dapr Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `dapr.enabled` | Enable Dapr sidecar | `true` |
| `dapr.appId` | Dapr app ID | `notification-service` |
| `dapr.appPort` | Application port | `8080` |
| `dapr.logLevel` | Dapr log level | `info` |

---

## 📝 Examples

### Custom Values File

Create `prod-values.yaml`:

```yaml
replicaCount: 5

image:
  repository: ghcr.io/your-org/notification-service
  tag: "v1.2.3"

resources:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20

kafka:
  bootstrapServers: "kafka-0.kafka:9092,kafka-1.kafka:9092,kafka-2.kafka:9092"

app:
  logLevel: "DEBUG"
  environment: "production"

secrets:
  sendgridApiKey: "U0cuYWJjMTIz..."  # Base64 encoded
  firebaseCredentials: "eyJwcm9qZ..."  # Base64 encoded
  databaseUrl: "cG9zdGdyZXNxbC..."  # Base64 encoded
```

Install with custom values:

```bash
helm install notification-service ./helm/notification-service -f prod-values.yaml
```

### Upgrade Deployment

```bash
# Upgrade with new values
helm upgrade notification-service ./helm/notification-service -f prod-values.yaml

# Upgrade with specific values
helm upgrade notification-service ./helm/notification-service \
  --set replicaCount=5 \
  --set image.tag=v1.2.4
```

### Rollback

```bash
# Rollback to previous version
helm rollback notification-service

# Rollback to specific revision
helm rollback notification-service 3
```

---

## 🔍 Testing

### Lint Chart

```bash
helm lint ./helm/notification-service
```

### Template Dry-Run

```bash
# Generate manifests without installing
helm template notification-service ./helm/notification-service

# Generate with specific values
helm template notification-service ./helm/notification-service -f prod-values.yaml
```

### Install Dry-Run

```bash
# Test installation without actually installing
helm install notification-service ./helm/notification-service --dry-run --debug
```

---

## 🐞 Troubleshooting

### Check Helm Release Status

```bash
helm status notification-service
helm history notification-service
```

### View Deployed Values

```bash
helm get values notification-service
```

### View Deployed Manifests

```bash
helm get manifest notification-service
```

### Debug Installation Issues

```bash
# Debug template rendering
helm template notification-service ./helm/notification-service --debug

# Check Helm hooks
helm get hooks notification-service
```

---

## 🧹 Uninstallation

```bash
# Uninstall release
helm uninstall notification-service

# Uninstall and delete namespace
helm uninstall notification-service --namespace todo-app
kubectl delete namespace todo-app
```

---

## 📦 Chart Structure

```
notification-service/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Default configuration values
├── .helmignore                   # Patterns to ignore
├── README.md                     # This file
└── templates/
    ├── _helpers.tpl              # Template helpers
    ├── deployment.yaml           # Deployment manifest
    ├── service.yaml              # Service manifest
    ├── configmap.yaml            # ConfigMap manifest
    ├── secrets.yaml              # Secrets manifest
    └── hpa.yaml                  # HorizontalPodAutoscaler manifest
```

---

## 🔐 Security Best Practices

1. **Secrets Management**:
   - Never commit base64-encoded secrets to version control
   - Use external secret management (Vault, Sealed Secrets, etc.)
   - Rotate secrets regularly

2. **Image Security**:
   - Use specific image tags (not `latest`)
   - Scan images for vulnerabilities
   - Use private registries for production

3. **Resource Limits**:
   - Always set CPU and memory limits
   - Prevent resource exhaustion attacks
   - Monitor resource usage

4. **Network Policies**:
   - Implement network policies for isolation
   - Restrict ingress/egress traffic
   - Use mTLS with Dapr

---

## 📊 Monitoring

### Prometheus Metrics

The notification service exposes metrics on `/metrics`:

- `notifications_sent_total` - Total notifications sent by channel
- `notification_delivery_latency_seconds` - Notification delivery latency
- `notification_failures_total` - Total notification failures

### Health Checks

- **Liveness**: `/health` - Service is alive
- **Readiness**: `/health` - Service is ready to accept traffic

---

## 📚 Additional Resources

- [Helm Documentation](https://helm.sh/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Dapr Documentation](https://docs.dapr.io/)

---

**Chart Version**: 1.0.0
**App Version**: 1.0.0
**Status**: ✅ Production Ready
**Maintainer**: Todo App Team
