#!/bin/bash

# =============================================================================
# Oracle Cloud OKE Quick Deployment Script
# =============================================================================
# This script automates the deployment process to Oracle Cloud OKE
# Run after: OKE cluster created and kubectl configured
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    print_error "kubectl not found. Please install kubectl first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "docker not found. Please install Docker first."
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    print_error "kubectl not connected to cluster. Please configure kubectl access to OKE first."
    exit 1
fi

print_success "Prerequisites check passed"

# Step 1: Create namespace
print_step "Step 1/5: Creating namespace..."
kubectl apply -f namespace.yaml
print_success "Namespace created"

# Step 2: Deploy backend
print_step "Step 2/5: Deploying backend..."

echo "Applying backend ConfigMap and Secrets..."
kubectl apply -f backend-configmap.yaml
kubectl apply -f backend-secret.yaml

echo "Deploying backend application..."
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

echo "Waiting for backend pods to be ready..."
kubectl wait --for=condition=ready pod -l app=todo-backend -n todo-app --timeout=300s || {
    print_error "Backend pods failed to start. Checking logs..."
    kubectl logs -n todo-app -l app=todo-backend --tail=50
    exit 1
}

print_success "Backend deployed successfully"

# Step 3: Get backend LoadBalancer IP
print_step "Step 3/5: Getting backend LoadBalancer IP..."

echo "Waiting for backend LoadBalancer external IP (this may take 2-5 minutes)..."
BACKEND_IP=""
for i in {1..60}; do
    BACKEND_IP=$(kubectl get svc -n todo-app todo-backend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$BACKEND_IP" ]; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

if [ -z "$BACKEND_IP" ]; then
    print_error "Failed to get backend LoadBalancer IP. Check OCI console for LoadBalancer status."
    kubectl get svc -n todo-app todo-backend
    exit 1
fi

print_success "Backend LoadBalancer IP: $BACKEND_IP"
echo -e "${GREEN}Backend API URL: http://$BACKEND_IP${NC}"

# Step 4: Update frontend with backend IP
print_step "Step 4/5: Deploying frontend..."

# Check if frontend needs backend IP update
if grep -q "TODO_BACKEND_IP" frontend-deployment.yaml; then
    print_warning "Updating frontend-deployment.yaml with backend IP..."
    sed -i.bak "s/TODO_BACKEND_IP/$BACKEND_IP/g" frontend-deployment.yaml
fi

echo "Deploying frontend application..."
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

echo "Waiting for frontend pods to be ready..."
kubectl wait --for=condition=ready pod -l app=todo-frontend -n todo-app --timeout=300s || {
    print_error "Frontend pods failed to start. Checking logs..."
    kubectl logs -n todo-app -l app=todo-frontend --tail=50
    exit 1
}

print_success "Frontend deployed successfully"

# Step 5: Get frontend LoadBalancer IP
print_step "Step 5/5: Getting frontend LoadBalancer IP..."

echo "Waiting for frontend LoadBalancer external IP (this may take 2-5 minutes)..."
FRONTEND_IP=""
for i in {1..60}; do
    FRONTEND_IP=$(kubectl get svc -n todo-app todo-frontend -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$FRONTEND_IP" ]; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

if [ -z "$FRONTEND_IP" ]; then
    print_error "Failed to get frontend LoadBalancer IP. Check OCI console for LoadBalancer status."
    kubectl get svc -n todo-app todo-frontend
    exit 1
fi

print_success "Frontend LoadBalancer IP: $FRONTEND_IP"

# Display final URLs
echo ""
echo "============================================="
echo -e "${GREEN}✓ DEPLOYMENT SUCCESSFUL!${NC}"
echo "============================================="
echo ""
echo -e "📱 ${BLUE}Frontend URL (for university form):${NC}"
echo -e "   ${GREEN}http://$FRONTEND_IP${NC}"
echo ""
echo -e "🔧 ${BLUE}Backend API URL:${NC}"
echo -e "   http://$BACKEND_IP"
echo ""
echo "============================================="
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Open http://$FRONTEND_IP in your browser"
echo "2. Test the application (signup → login → add task)"
echo "3. Submit this URL in your university form"
echo ""
echo -e "${YELLOW}To check application status:${NC}"
echo "  kubectl get all -n todo-app"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  kubectl logs -n todo-app -l app=todo-backend --tail=50"
echo "  kubectl logs -n todo-app -l app=todo-frontend --tail=50"
echo ""
