#!/bin/bash

# Port configurations
BACKEND_PORT=8000
AGENT_PORT=9000
FRONTEND_PORT=3000

# Color outputs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Starting Claude Remote ===${NC}"

# Find local IP address
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n 1 | awk '{print $2}')
echo -e "${YELLOW}Local IP discovered: ${LOCAL_IP}${NC}"

# Kill any existing processes on these ports to prevent port conflicts
echo "Cleaning up any old processes running on ports $BACKEND_PORT, $AGENT_PORT, $FRONTEND_PORT..."
lsof -ti :$BACKEND_PORT | xargs kill -9 2>/dev/null
lsof -ti :$AGENT_PORT | xargs kill -9 2>/dev/null
lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null

# Activate virtual environment and check dependencies
if [ ! -d ".venv" ]; then
    echo "Creating python virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r backend/requirements.txt -r agent/requirements.txt
fi

# Start Backend
echo "Starting backend on port $BACKEND_PORT..."
cd backend
../.venv/bin/uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Start Agent
echo "Starting desktop agent on port $AGENT_PORT..."
cd agent
../.venv/bin/uvicorn desktop_agent:app --host 127.0.0.1 --port $AGENT_PORT > ../agent.log 2>&1 &
AGENT_PID=$!
cd ..

# Start Frontend
echo "Starting frontend on port $FRONTEND_PORT..."
cd frontend
npx next dev -H 0.0.0.0 -p $FRONTEND_PORT > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Function to kill all background jobs on exit
cleanup() {
    echo -e "\n${BLUE}=== Stopping Claude Remote ===${NC}"
    echo "Stopping frontend (PID $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    echo "Stopping agent (PID $AGENT_PID)..."
    kill $AGENT_PID 2>/dev/null
    echo "Stopping backend (PID $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}Claude Remote is running successfully!${NC}"
echo -e "Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC} or ${GREEN}http://$LOCAL_IP:$FRONTEND_PORT${NC} (from phone)"
echo -e "Backend:  ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "Logs are saved to backend.log, agent.log, and frontend.log"
echo -e "${YELLOW}Press [Ctrl+C] to stop all services.${NC}"

# Keep script running
while true; do
    sleep 1
done
