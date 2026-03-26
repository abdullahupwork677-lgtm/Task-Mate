# Oracle Cloud OKE Deployment

**Quick deployment guide for Oracle Kubernetes Engine**

---

## 🚀 Quick Start (For University Submission)

### Prerequisites (5 min)
1. Oracle Cloud account: https://cloud.oracle.com
2. kubectl installed
3. Docker installed

### Step 1: Create OKE Cluster (20 min)

**Oracle Cloud Console → Developer Services → Kubernetes Clusters → Create Cluster**

```
Quick Create Settings:
- Name: todo-app-cluster
- Kubernetes Version: Latest
- Node Count: 2
- Shape: VM.Standard.E4.Flex (1 OCPU, 16 GB)
```

Wait for cluster status: **Active** ✅

### Step 2: Configure kubectl (2 min)

In Oracle Cloud Console → Your Cluster → "Access Cluster":
- Copy the "Local Access" command
- Run it in terminal

Test:
```bash
kubectl get nodes
```

### Step 3: Configure Secrets (3 min)

Edit `backend-secret.yaml`:
```yaml
DATABASE_URL: "your-neon-postgresql-url"
BETTER_AUTH_SECRET: "your-32-char-secret"
OPENAI_API_KEY: "your-openai-key"
```

### Step 4: Update Docker Images (2 min)

Edit `backend-deployment.yaml` and `frontend-deployment.yaml`:
```yaml
image: ghcr.io/YOUR_USERNAME/todo-backend:latest
image: ghcr.io/YOUR_USERNAME/todo-frontend:latest
```

### Step 5: Deploy (5 min)

```bash
cd k8s/oke
./deploy.sh
```

**Wait for final output:**
```
✓ DEPLOYMENT SUCCESSFUL!
📱 Frontend URL (for university form):
   http://140.238.X.X
```

**Submit this URL in your form!** ✅

---

## 📋 Manual Deployment Steps

If you prefer manual deployment, follow [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) for complete step-by-step instructions.

---

## 🔍 Verify Deployment

```bash
# Check all resources
kubectl get all -n todo-app

# Check pods status
kubectl get pods -n todo-app

# Check services and get IPs
kubectl get svc -n todo-app
```

---

## 📊 Monitor Application

```bash
# Backend logs
kubectl logs -n todo-app -l app=todo-backend -f

# Frontend logs
kubectl logs -n todo-app -l app=todo-frontend -f

# Pod details
kubectl describe pod -n todo-app POD_NAME
```

---

## 🛠️ Troubleshooting

### Pods not starting?
```bash
kubectl describe pod -n todo-app POD_NAME
kubectl logs -n todo-app POD_NAME
```

### LoadBalancer stuck on <pending>?
- Wait 5 minutes (OCI LoadBalancer takes time)
- Check OCI Console → Networking → Load Balancers

### Backend health check failing?
```bash
# Check database connection
kubectl logs -n todo-app -l app=todo-backend | grep -i database

# Verify secrets are set
kubectl get secret -n todo-app backend-secrets -o yaml
```

---

## 🧹 Cleanup (After Submission)

```bash
# Delete all resources
kubectl delete namespace todo-app

# Or delete entire cluster from OCI Console
```

---

## 📁 Files Overview

```
k8s/oke/
├── README.md                      # This file
├── DEPLOYMENT_GUIDE.md            # Detailed step-by-step guide
├── deploy.sh                      # Automated deployment script
├── namespace.yaml                 # Namespace definition
├── backend-configmap.yaml         # Backend environment variables
├── backend-secret.yaml            # Backend secrets (edit this!)
├── backend-deployment.yaml        # Backend pods
├── backend-service.yaml           # Backend LoadBalancer
├── frontend-deployment.yaml       # Frontend pods
└── frontend-service.yaml          # Frontend LoadBalancer
```

---

## 🎯 Next Steps

After successful deployment:
1. ✅ Test application in browser
2. ✅ Submit URL in university form
3. ✅ Keep deployment running for evaluation
4. ✅ Continue Phase 5 implementation (recurring tasks)

---

## 📞 Need Help?

- **Deployment issues:** See [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) troubleshooting section
- **Oracle Cloud docs:** https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm
- **Kubernetes docs:** https://kubernetes.io/docs/

---

**Total Time:** 35-40 minutes from start to final URL ⚡

**Success!** 🎉
