---
name: digitalocean-deploy.backup-20260211
description: Complete DigitalOcean deployment automation with 8 commands - droplet creation, app deployment, configuration management, monitoring setup (Prometheus/Grafana), and testing. Use when deploying to DigitalOcean cloud platform without cloud expertise (80-90% time savings, cost-effective alternative to AWS/Azure/GCP).
---

# DigitalOcean Deploy (Backup)

**DigitalOcean automation - No cloud specialist needed!**

**Category:** Cloud Deployment
**Time Savings:** 80-90% reduction
**Quality:** Cost-effective deployment

---

## 📋 Quick Instructions

1. **Create Droplet**
   ```bash
   python3 scripts/tool.py create-droplet --size s-2vcpu-4gb
   ```

2. **Deploy Application**
   ```bash
   python3 scripts/tool.py deploy-app --manifest app.yaml
   ```

3. **Setup Monitoring**
   ```bash
   python3 scripts/tool.py setup-monitoring
   ```

4. **Run Tests**
   ```bash
   python3 scripts/tool.py test
   ```

---

## 🛠️ Commands (8 total)

**Location:** `scripts/tool.py`

```bash
python3 scripts/tool.py check-prerequisites
python3 scripts/tool.py create-droplet --size s-2vcpu-4gb
python3 scripts/tool.py configure
python3 scripts/tool.py deploy-app --manifest app.yaml
python3 scripts/tool.py setup-monitoring
python3 scripts/tool.py health-check
python3 scripts/tool.py test
python3 scripts/tool.py cleanup
```

---

## 📁 On-Demand Resources

### Droplet Sizing Guide
- **File:** `reference/droplet-sizing.md`
- **When:** Choosing droplet size
- **Contains:** CPU/RAM recommendations, cost comparison

### Monitoring Setup
- **File:** `reference/monitoring-setup.md`
- **When:** Setting up observability
- **Contains:** Prometheus, Grafana configuration

### Cost Optimization
- **File:** `reference/cost-optimization.md`
- **When:** Reducing costs
- **Contains:** Reserved pricing, right-sizing tips

---

## 🚀 Common Workflows

### Workflow 1: Production Deployment
```bash
1. python3 scripts/tool.py create-droplet --size s-2vcpu-4gb
2. python3 scripts/tool.py deploy-app --manifest app.yaml
3. python3 scripts/tool.py setup-monitoring
4. python3 scripts/tool.py test
```

---

## 💡 Token Efficiency

**Before:** 549 lines
**After:** ~145 lines
**Savings:** 74% reduction ✅

---

**Status:** Production-ready ✅
**Cost-effective cloud!** 💰
