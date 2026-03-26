# Oracle Cloud OKE Deployment Guide

**Complete guide to deploy Todo Chatbot to Oracle Cloud Kubernetes Engine (OKE)**

**Estimated Time:** 40-50 minutes

---

## Prerequisites

1. Oracle Cloud account (https://cloud.oracle.com)
2. Docker installed locally
3. kubectl installed locally
4. Git access to push Docker images
5. Database credentials (Neon PostgreSQL)
6. OpenAI API key

---

## Part 1: Oracle Cloud Setup (20-30 minutes)

### Step 1.1: Create OKE Cluster (20 minutes)

1. **Login to Oracle Cloud Console**
   - Go to: https://cloud.oracle.com
   - Sign in with your account

2. **Navigate to OKE**
   - Menu (☰) → Developer Services → Kubernetes Clusters (OKE)

3. **Create Cluster**
   - Click **"Create Cluster"**
   - Select **"Quick Create"** (recommended for fastest setup)

4. **Configure Cluster:**
   ```
   Name: todo-app-cluster
   Kubernetes Version: Latest (v1.28+)
   Visibility Type: Public Endpoint
   Shape: VM.Standard.E4.Flex
   Node Pool:
     - Name: pool1
     - Node Count: 2
     - Shape: VM.Standard.E4.Flex
     - OCPUs: 1 per node
     - Memory: 16 GB per node
   ```

5. **Click "Create Cluster"**
   - Wait 15-20 minutes for cluster creation
   - Status will change from "Creating" → "Active"

### Step 1.2: Configure kubectl Access (5 minutes)

1. **Install OCI CLI** (if not installed):
   ```bash
   bash -c "$(curl -L https://raw.githubusercontent.com/oracle/oci-cli/master/scripts/install/install.sh)"
   ```

2. **Configure OCI CLI:**
   ```bash
   oci setup config
   ```
   Follow prompts to enter:
   - User OCID (from Profile → User Settings)
   - Tenancy OCID (from Profile → Tenancy)
   - Region (e.g., us-ashburn-1)
   - Generate new API key (Y)

3. **Get kubeconfig for OKE Cluster:**

   In Oracle Cloud Console:
   - Go to your cluster → "Access Cluster"
   - Copy the "Local Access" command (looks like):
   ```bash
   oci ce cluster create-kubeconfig --cluster-id ocid1.cluster.oc1... --file $HOME/.kube/config --region us-ashburn-1 --token-version 2.0.0  --kube-endpoint PUBLIC_ENDPOINT
   ```
   - Run the command in your terminal

4. **Verify kubectl access:**
   ```bash
   kubectl get nodes
   ```
   Should show 2 nodes in "Ready" state.

---

## Part 2: Build & Push Docker Images (10 minutes)

### Step 2.1: Build Backend Image

```bash
# Navigate to project root
cd /Users/apple/Documents/Projects/todo_phase5

# Build backend image
cd backend
docker build -t ghcr.io/YOUR_GITHUB_USERNAME/todo-backend:latest .

# Test locally (optional)
docker run -p 8000:8000 ghcr.io/YOUR_GITHUB_USERNAME/todo-backend:latest
```

### Step 2.2: Build Frontend Image

```bash
# Build frontend image with backend API URL
cd ../frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://WILL_UPDATE_LATER \
  -t ghcr.io/YOUR_GITHUB_USERNAME/todo-frontend:latest .
```

### Step 2.3: Push to GitHub Container Registry

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Push images
docker push ghcr.io/YOUR_GITHUB_USERNAME/todo-backend:latest
docker push ghcr.io/YOUR_GITHUB_USERNAME/todo-frontend:latest
```

**Alternative:** Use Docker Hub instead of GHCR:
```bash
docker tag ghcr.io/YOUR_GITHUB_USERNAME/todo-backend:latest YOUR_DOCKERHUB_USERNAME/todo-backend:latest
docker push YOUR_DOCKERHUB_USERNAME/todo-backend:latest
```

---

## Part 3: Configure Secrets (5 minutes)

### Step 3.1: Update backend-secret.yaml

Edit `k8s/oke/backend-secret.yaml`:

```yaml
stringData:
  # Your Neon PostgreSQL connection string
  DATABASE_URL: "postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech:5432/neondb?sslmode=require"

  # Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
  BETTER_AUTH_SECRET: "YOUR_32_CHAR_SECRET_HERE"

  # Your OpenAI API key
  OPENAI_API_KEY: "sk-proj-YOUR_KEY_HERE"
```

### Step 3.2: Update Deployment Images

Edit `k8s/oke/backend-deployment.yaml`:
```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/todo-backend:latest
```

Edit `k8s/oke/frontend-deployment.yaml`:
```yaml
image: ghcr.io/YOUR_GITHUB_USERNAME/todo-frontend:latest
```

---

## Part 4: Deploy to OKE (10 minutes)

### Step 4.1: Create Namespace

```bash
cd /Users/apple/Documents/Projects/todo_phase5/k8s/oke

kubectl apply -f namespace.yaml
```

### Step 4.2: Deploy Backend

```bash
# Apply ConfigMap and Secrets
kubectl apply -f backend-configmap.yaml
kubectl apply -f backend-secret.yaml

# Deploy backend
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# Check backend deployment
kubectl get pods -n todo-app -l app=todo-backend
kubectl logs -n todo-app -l app=todo-backend --tail=50
```

### Step 4.3: Get Backend LoadBalancer IP

```bash
# Wait for LoadBalancer external IP (takes 2-5 minutes)
kubectl get svc -n todo-app todo-backend -w

# Once EXTERNAL-IP shows (not <pending>), copy the IP
# Example output:
# NAME            TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
# todo-backend    LoadBalancer   10.96.50.123    140.238.x.x     80:30123/TCP   3m
```

**Save this IP for form submission:** `http://BACKEND_EXTERNAL_IP`

### Step 4.4: Update Frontend with Backend IP

Edit `k8s/oke/frontend-deployment.yaml`:
```yaml
env:
- name: NEXT_PUBLIC_API_URL
  value: "http://BACKEND_EXTERNAL_IP"  # Replace with actual IP from above
```

Apply updated frontend:
```bash
kubectl apply -f frontend-deployment.yaml
```

**OR rebuild frontend with correct API URL:**
```bash
cd ../../frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://BACKEND_EXTERNAL_IP \
  -t ghcr.io/YOUR_GITHUB_USERNAME/todo-frontend:latest .
docker push ghcr.io/YOUR_GITHUB_USERNAME/todo-frontend:latest

# Then apply
cd ../k8s/oke
kubectl apply -f frontend-deployment.yaml
```

### Step 4.5: Deploy Frontend

```bash
# Deploy frontend service
kubectl apply -f frontend-service.yaml

# Check frontend deployment
kubectl get pods -n todo-app -l app=todo-frontend
kubectl logs -n todo-app -l app=todo-frontend --tail=50
```

### Step 4.6: Get Frontend LoadBalancer IP

```bash
# Wait for LoadBalancer external IP
kubectl get svc -n todo-app todo-frontend -w

# Once EXTERNAL-IP shows:
# NAME             TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)        AGE
# todo-frontend    LoadBalancer   10.96.60.234    140.238.y.y     80:30456/TCP   3m
```

---

## Part 5: Test & Get Final URL (5 minutes)

### Step 5.1: Access Application

**Frontend URL (for university form):**
```
http://FRONTEND_EXTERNAL_IP
```

Example: `http://140.238.45.67`

### Step 5.2: Test Application

1. **Open frontend URL in browser**
2. **Create account** (signup)
3. **Login**
4. **Test chat:** "Add a task to buy milk"
5. **Verify task appears**

### Step 5.3: Verify All Services

```bash
# Check all resources
kubectl get all -n todo-app

# Check logs for errors
kubectl logs -n todo-app -l app=todo-backend --tail=100
kubectl logs -n todo-app -l app=todo-frontend --tail=100

# Check service endpoints
kubectl get endpoints -n todo-app
```

---

## Final URL for University Form

**Submit this URL:**
```
http://FRONTEND_EXTERNAL_IP
```

Example: `http://140.238.45.67`

**Deployment Architecture:**
- Platform: Oracle Cloud Infrastructure (OCI)
- Kubernetes: Oracle Kubernetes Engine (OKE)
- Backend: FastAPI + PostgreSQL (Neon)
- Frontend: Next.js
- High Availability: 2 replicas each for backend & frontend
- Load Balancer: OCI Flexible Load Balancer

---

## Troubleshooting

### Pods not starting:
```bash
kubectl describe pod -n todo-app POD_NAME
kubectl logs -n todo-app POD_NAME --previous  # if crashed
```

### LoadBalancer pending:
- OCI LoadBalancer takes 2-5 minutes to provision
- Check OCI Console → Networking → Load Balancers
- Verify security rules allow inbound traffic on port 80

### Backend health check failing:
```bash
# Check backend logs
kubectl logs -n todo-app -l app=todo-backend

# Check database connectivity
kubectl exec -n todo-app -it BACKEND_POD_NAME -- curl http://localhost:8000/health
```

### Frontend can't reach backend:
```bash
# Verify NEXT_PUBLIC_API_URL is set correctly
kubectl describe pod -n todo-app FRONTEND_POD_NAME | grep NEXT_PUBLIC_API_URL

# Test backend from frontend pod
kubectl exec -n todo-app -it FRONTEND_POD_NAME -- wget -O- http://todo-backend/health
```

---

## Monitoring & Maintenance

### View Logs:
```bash
# Backend logs
kubectl logs -n todo-app -l app=todo-backend -f

# Frontend logs
kubectl logs -n todo-app -l app=todo-frontend -f
```

### Scale Replicas:
```bash
# Scale backend to 3 replicas
kubectl scale deployment -n todo-app todo-backend --replicas=3

# Scale frontend to 3 replicas
kubectl scale deployment -n todo-app todo-frontend --replicas=3
```

### Update Application:
```bash
# After pushing new Docker images
kubectl rollout restart deployment -n todo-app todo-backend
kubectl rollout restart deployment -n todo-app todo-frontend

# Check rollout status
kubectl rollout status deployment -n todo-app todo-backend
```

---

## Cleanup (After Submission)

**To delete everything:**
```bash
# Delete namespace (removes all resources)
kubectl delete namespace todo-app

# Delete OKE cluster (from Oracle Cloud Console)
# Menu → Developer Services → Kubernetes Clusters → Delete
```

---

## Cost Estimation

**Oracle Cloud Free Tier:**
- Always Free: 2 VMs (VM.Standard.E2.1.Micro)
- OKE cluster management: Free
- LoadBalancer: Free for first 10 Mbps

**If using paid resources:**
- VM.Standard.E4.Flex (1 OCPU, 16 GB): ~$0.03/hour
- 2 nodes: ~$0.06/hour = ~$1.44/day
- LoadBalancers: Included

**Recommendation:** Use for demo/submission, then cleanup to avoid charges.

---

## Next Steps

After form submission:
1. ✅ Keep deployment running for evaluation
2. ✅ Continue Phase 5 implementation (recurring tasks)
3. ✅ Add monitoring (Prometheus/Grafana)
4. ✅ Set up CI/CD (GitHub Actions)
5. ✅ Configure custom domain (optional)

---

**Questions?** Check troubleshooting section or Oracle Cloud documentation.

**Success!** 🎉 Your Todo Chatbot is now deployed on Oracle Cloud!
