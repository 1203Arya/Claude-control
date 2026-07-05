import json
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Claude Remote Backend")

# Allow CORS for everything (development and home network access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active connections
agent_websocket: Optional[WebSocket] = None
frontend_websockets: Set[WebSocket] = set()

# Pending requests state: request_id -> dict
pending_requests: Dict[str, dict] = {}

def get_state():
    return {
        "type": "state_update",
        "agent_connected": agent_websocket is not None,
        "pending_requests": list(pending_requests.values())
    }

async def broadcast_to_frontends(message: dict):
    if not frontend_websockets:
        return
    msg_str = json.dumps(message)
    disconnected = set()
    for ws in frontend_websockets:
        try:
            await ws.send_text(msg_str)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        frontend_websockets.discard(ws)

@app.get("/status")
def status():
    return get_state()

@app.websocket("/ws/agent")
async def ws_agent(websocket: WebSocket):
    global agent_websocket
    await websocket.accept()
    print("Desktop agent connected!")
    agent_websocket = websocket
    
    # Broadcast connection state update to frontends
    await broadcast_to_frontends(get_state())
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            print(f"Received message from agent: {payload}")
            
            msg_type = payload.get("type")
            if msg_type == "permission_request":
                req_id = payload.get("request_id")
                pending_requests[req_id] = {
                    "request_id": req_id,
                    "tool_name": payload.get("tool_name"),
                    "tool_input": payload.get("tool_input"),
                    "session_id": payload.get("session_id"),
                }
                # Broadcast the new request to frontends
                await broadcast_to_frontends({
                    "type": "new_request",
                    "request": pending_requests[req_id]
                })
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        print("Desktop agent disconnected!")
    except Exception as e:
        print(f"Error in agent connection: {e}")
    finally:
        agent_websocket = None
        await broadcast_to_frontends(get_state())

@app.websocket("/ws/frontend")
async def ws_frontend(websocket: WebSocket):
    await websocket.accept()
    print("Frontend client connected!")
    frontend_websockets.add(websocket)
    
    # Send current state immediately on connection
    try:
        await websocket.send_text(json.dumps(get_state()))
    except Exception:
        frontend_websockets.discard(websocket)
        return
        
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            print(f"Received message from frontend: {payload}")
            
            msg_type = payload.get("type")
            if msg_type == "action":
                req_id = payload.get("request_id")
                approved = payload.get("approved")
                
                # Check if it exists in pending
                if req_id in pending_requests:
                    pending_requests.pop(req_id)
                    # Forward the action response to the agent
                    if agent_websocket:
                        try:
                            await agent_websocket.send_text(json.dumps({
                                "type": "permission_response",
                                "request_id": req_id,
                                "approved": approved
                            }))
                        except Exception as e:
                            print(f"Failed to forward response to agent: {e}")
                    # Broadcast resolution to all frontends
                    await broadcast_to_frontends({
                        "type": "request_resolved",
                        "request_id": req_id,
                        "approved": approved
                    })
            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        print("Frontend client disconnected!")
    except Exception as e:
        print(f"Error in frontend connection: {e}")
    finally:
        frontend_websockets.discard(websocket)
