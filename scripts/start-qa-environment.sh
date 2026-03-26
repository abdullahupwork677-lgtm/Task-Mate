#!/bin/bash
# Quick start script for Manual QA Environment (T214)
# Phase V - Due Dates & Reminders

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Manual QA Environment Setup - Phase V                   ║"
echo "║  Task: T214                                              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${RED}✗ Error: backend/ directory not found${NC}"
    echo "  Run this script from project root: todo_phase5/"
    exit 1
fi

# Check if venv exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment found${NC}"
fi

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠ DATABASE_URL not set in environment${NC}"
    echo "  Export DATABASE_URL or create backend/.env file"
    echo "  Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/todo_db'"
fi

# Check OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}⚠ OPENAI_API_KEY not set${NC}"
    echo "  Chatbot functionality will not work without OpenAI API key"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo " Service Startup Options"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Select services to start:"
echo "  1) Backend API only (minimal for basic QA)"
echo "  2) Backend API + Frontend (for UI validation)"
echo "  3) Full stack (Backend + Frontend + Kafka + Notification service)"
echo "  4) Exit"
echo ""
read -p "Enter option (1-4): " option

case $option in
    1)
        echo ""
        echo -e "${GREEN}Starting Backend API...${NC}"
        echo ""
        cd backend
        source venv/bin/activate

        # Check if migrations need to be run
        echo "Checking database migrations..."
        alembic current 2>/dev/null || {
            echo -e "${YELLOW}Running database migrations...${NC}"
            alembic upgrade head
        }

        echo ""
        echo -e "${GREEN}✓ Backend API ready${NC}"
        echo "  URL: http://localhost:8000"
        echo "  Health: http://localhost:8000/health"
        echo "  Docs: http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""

        uvicorn src.main:app --reload
        ;;

    2)
        echo ""
        echo -e "${GREEN}Starting Backend API + Frontend...${NC}"
        echo ""

        # Start backend in background
        cd backend
        source venv/bin/activate

        echo "Checking database migrations..."
        alembic current 2>/dev/null || {
            echo -e "${YELLOW}Running database migrations...${NC}"
            alembic upgrade head
        }

        echo ""
        echo -e "${GREEN}✓ Starting backend API...${NC}"
        uvicorn src.main:app --reload > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo "  Backend PID: $BACKEND_PID"
        cd ..

        # Wait for backend to start
        sleep 3

        # Start frontend
        cd frontend
        echo ""
        echo -e "${GREEN}✓ Starting frontend...${NC}"

        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi

        npm run dev > ../logs/frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo "  Frontend PID: $FRONTEND_PID"
        cd ..

        echo ""
        echo -e "${GREEN}✓ Services started${NC}"
        echo "  Backend: http://localhost:8000"
        echo "  Frontend: http://localhost:3000"
        echo "  Logs: logs/backend.log, logs/frontend.log"
        echo ""
        echo "To stop services:"
        echo "  kill $BACKEND_PID $FRONTEND_PID"
        echo ""
        echo "Press Ctrl+C to stop monitoring..."

        # Monitor logs
        tail -f logs/backend.log logs/frontend.log
        ;;

    3)
        echo ""
        echo -e "${YELLOW}Full stack mode requires:${NC}"
        echo "  - Kafka/Redpanda running"
        echo "  - Dapr runtime installed"
        echo "  - Notification service configured"
        echo ""
        echo "This is an advanced setup. Refer to:"
        echo "  - k8s/DEPLOYMENT_GUIDE.md for Kubernetes deployment"
        echo "  - backend/README.md for Kafka setup"
        echo "  - services/notification/README.md for notification service"
        echo ""
        exit 0
        ;;

    4)
        echo "Exiting..."
        exit 0
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac
