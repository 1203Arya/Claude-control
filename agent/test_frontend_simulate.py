import asyncio
import json
import websockets

async def simulate_frontend_approval():
    url = "ws://localhost:8000/ws/frontend"
    print(f"Connecting to frontend WebSocket at {url}...")
    try:
        async with websockets.connect(url) as ws:
            print("Connected to frontend WebSocket!")
            
            while True:
                message = await ws.recv()
                data = json.loads(message)
                print(f"Received from backend: {data}")
                
                # Check for state update or new request
                if data.get("type") == "state_update":
                    pending = data.get("pending_requests", [])
                    if pending:
                        req = pending[0]
                        req_id = req["request_id"]
                        print(f"Found pending request {req_id}. Sending approval...")
                        await ws.send(json.dumps({
                            "type": "action",
                            "request_id": req_id,
                            "approved": True
                        }))
                        print("Approval sent!")
                        break
                elif data.get("type") == "new_request":
                    req_id = data["request"]["request_id"]
                    print(f"Received new request {req_id}. Sending approval...")
                    await ws.send(json.dumps({
                        "type": "action",
                        "request_id": req_id,
                        "approved": True
                    }))
                    print("Approval sent!")
                    break
    except Exception as e:
        print(f"Error in frontend simulator: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_frontend_approval())
