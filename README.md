# Claude Control 🎮

Control Claude Code from your phone. Every file write, bash command, or edit triggers a real-time Approve/Deny notification — Claude waits for your decision before proceeding.

## How it works
1. Claude Code fires a `PreToolUse` hook before every action
2. Hook sends the request to a local desktop agent
3. Agent forwards it to backend via WebSocket
4. Phone receives Approve/Deny request
5. Claude waits for your decision

## Stack
Python · FastAPI · WebSockets · ngrok · Claude Code Hooks · Next.js

## Setup

### 1. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Agent
```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. ngrok
```bash
ngrok config add-authtoken YOUR_TOKEN
```

### 4. Run
```bash
claude
```
