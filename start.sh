#!/bin/bash
echo "🚀 Claude Remote starting..."

kill $(lsof -ti:8000,9000) 2>/dev/null
pkill -f ngrok 2>/dev/null
sleep 1

cd ~/Desktop/"claude remote"/backend
source .venv/bin/activate 2>/dev/null
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo "✅ Backend started"
sleep 2

ngrok http --url=copier-aviation-underwent.ngrok-free.dev 8000 > /tmp/ngrok.log 2>&1 &
echo "✅ ngrok started (fixed domain)"
sleep 2

cd ~/Desktop/"claude remote"/agent
source .venv/bin/activate 2>/dev/null
python3 -m uvicorn desktop_agent:app --host 127.0.0.1 --port 9000 > /tmp/agent.log 2>&1 &
echo "✅ Agent started"
sleep 2

echo "✅ Sab ready!"
