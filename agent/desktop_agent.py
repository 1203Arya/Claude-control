import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import websockets

# Configuration
BACKEND_WS_URL = "ws://localhost:8000/ws/agent"

# State
# request_id -> {"event": asyncio.Event, "approved": bool}
pending_local_requests = {}
backend_ws = None

async def listen_to_backend():
    global backend_ws
    while True:
        try:
            print(f"Connecting to backend at {BACKEND_WS_URL}...")
            async with websockets.connect(BACKEND_WS_URL) as ws:
                backend_ws = ws
                print("Connected to backend!")
                while True:
                    message_str = await ws.recv()
                    payload = json.loads(message_str)
                    print(f"Received from backend: {payload}")
                    
                    msg_type = payload.get("type")
                    if msg_type == "permission_response":
                        req_id = payload.get("request_id")
                        approved = payload.get("approved")
                        if req_id in pending_local_requests:
                            pending_local_requests[req_id]["approved"] = approved
                            pending_local_requests[req_id]["event"].set()
        except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError, Exception) as e:
            print(f"Connection error: {e}. Retrying in 3 seconds...")
            backend_ws = None
            await asyncio.sleep(3)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(listen_to_backend())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

@app.post("/request")
async def handle_request(request: Request):
    global backend_ws
    payload = await request.json()
    print(f"Received request from hook: {payload}")
    
    if not backend_ws:
        print("Backend not connected! Rejecting hook request.")
        return JSONResponse(status_code=503, content={"error": "Backend not connected"})
        
    req_id = str(uuid.uuid4())
    event = asyncio.Event()
    pending_local_requests[req_id] = {
        "event": event,
        "approved": False
    }
    
    request_payload = {
        "type": "permission_request",
        "request_id": req_id,
        "tool_name": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "session_id": payload.get("session_id")
    }
    
    try:
        await backend_ws.send(json.dumps(request_payload))
    except Exception as e:
        print(f"Failed to send request to backend: {e}")
        pending_local_requests.pop(req_id)
        return JSONResponse(status_code=500, content={"error": "Failed to communicate with backend"})
        
    try:
        await asyncio.wait_for(event.wait(), timeout=300)
    except asyncio.TimeoutError:
        print(f"Request {req_id} timed out waiting for approval.")
        pending_local_requests.pop(req_id)
        return {"approved": False, "error": "Timeout"}
        
    res = pending_local_requests.pop(req_id)
    return {"approved": res["approved"]}
