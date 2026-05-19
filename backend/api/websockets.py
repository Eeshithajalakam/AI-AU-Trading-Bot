from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
import time
from typing import List

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# Background task to simulate live market data broadcasting
# In a real app, this would listen to Redis Pub/Sub from a worker
async def market_data_broadcaster():
    current_price = 2350.00
    while True:
        try:
            if manager.active_connections:
                # Random walk simulation
                import random
                from datetime import datetime
                
                current_price += (random.random() - 0.48) * 2.0
                
                message = json.dumps({
                    "type": "PRICE_UPDATE",
                    "price": round(current_price, 2),
                    "timestamp": datetime.utcnow().isoformat()
                })
                await manager.broadcast(message)
        except Exception as e:
            print(f"Broadcaster error: {e}")
            
        await asyncio.sleep(1.0) # Broadcast every 1 second

@router.websocket("/ws/trading")
async def websocket_trading_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial data
    import random
    from datetime import datetime, timedelta
    
    # Mock history
    history = []
    p = 2350.00
    now = datetime.utcnow()
    for i in range(60, 0, -1):
        t = now - timedelta(seconds=i)
        p += (random.random() - 0.48) * 1.5
        history.append({
            "time": t.isoformat(),
            "price": round(p, 2)
        })
        
    initial_signals = [
        {
            "id": "sig-1", "type": "LONG", "asset": "XAU/USD",
            "confidence": 94, "entry": 2345.50, "target": 2360.00,
            "stopLoss": 2335.00, "timestamp": int(time.time() * 1000), "active": True
        }
    ]
    
    await websocket.send_text(json.dumps({
        "type": "INITIAL_DATA",
        "history": history,
        "signals": initial_signals
    }))
    
    try:
        while True:
            # Keep connection alive, listen for client messages if any
            data = await websocket.receive_text()
            print(f"Received from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket Error: {e}")
        manager.disconnect(websocket)
